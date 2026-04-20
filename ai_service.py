import re
import json
from config import pc, index, EMBED_MODEL, hf_client, PROMPT, HF_MODEL
from database import db_manager
from transfers import (
    prepare_transfer,
    confirm_transfer,
    cancel_transfer,
    get_pending_transfer,
    get_account_balance,
    get_sender_account,
)


MODEL_NAME = HF_MODEL
BASE_PROMPT = PROMPT or "You are a helpful banking customer service assistant."

def clean_ai_response(text: str):
    if not text: return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'^\|.*\|\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s|:-]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

async def search_bank_knowledge(query: str):
    query_embedding = pc.inference.embed(
        model=EMBED_MODEL,
        inputs=[query],
        parameters={"input_type": "query"}
    )
    
    search_results = index.query(
        vector=query_embedding[0].values,
        top_k=3,
        include_metadata=True
    )
    
    return "\n".join([res.metadata['original_text'] for res in search_results.matches])

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_bank_knowledge",
            "description": "Use this tool to search the official Hadhramout Bank profile for accurate information about services, organizational structure, capital, and policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'What is Hadhramout Bank capital?' or 'individual services')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_account_balance",
            "description": "Use this tool when the user wants to check their own account balance. The server identifies the current user from request context.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_money_transfer",
            "description": "Use this tool when the user wants to transfer money. The server identifies the sender from request context, looks up the receiver by account serial ID, stores a pending transfer, and returns the receiver name for confirmation before any money is sent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "receiver_serial_id": {
                        "type": "string",
                        "description": "The serial ID of the receiver account."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to transfer. Ask the user for it if missing."
                    }
                },
                "required": ["receiver_serial_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_money_transfer",
            "description": "Use this tool only after the user confirms that the receiver account is correct and the transfer should proceed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_money_transfer",
            "description": "Use this tool when the user says the receiver is wrong or wants to stop a pending money transfer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_money_transfer",
            "description": "Use this tool to inspect the current pending transfer for the current user before asking for confirmation or when the user asks about the transfer details.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_illusion_account",
            "description": "Use this tool when the user needs an illusion account created for testing purposes. Requires the user's name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_name": {
                        "type": "string",
                        "description": "The name of the user for the illusion account."
                    }
                },
                "required": ["user_name"]
            }
        }
    }
]


async def run_tool(tool_name: str, args: dict, telegram_id: int):
    if tool_name == "search_bank_knowledge":
        return await search_bank_knowledge(args["query"])
    if tool_name == "check_account_balance":
        return json.dumps(get_account_balance(telegram_id), ensure_ascii=False)
    if tool_name == "prepare_money_transfer":
        return json.dumps(
            prepare_transfer(
                telegram_id=telegram_id,
                receiver_serial_id=args["receiver_serial_id"],
                amount=args.get("amount"),
            ),
            ensure_ascii=False,
        )
    if tool_name == "confirm_money_transfer":
        return json.dumps(confirm_transfer(telegram_id), ensure_ascii=False)
    if tool_name == "cancel_money_transfer":
        return json.dumps(cancel_transfer(telegram_id), ensure_ascii=False)
    if tool_name == "get_pending_money_transfer":
        return json.dumps(get_pending_transfer(telegram_id), ensure_ascii=False)
    if tool_name == "create_illusion_account":
        return json.dumps(get_sender_account(telegram_id, args["user_name"]), ensure_ascii=False)
    return json.dumps({"success": False, "message": f"Unknown tool: {tool_name}"}, ensure_ascii=False)

async def get_ai_response(user_query: str, telegram_id: int):
    conversation_history = []
    if db_manager:
        raw_history = db_manager.get_conversation_history(telegram_id, limit=6)
        raw_history.reverse()
        for msg in raw_history:
            if msg.get('message_text'):
                role = "user" if msg['message_type'] == 'user' else "assistant"
                conversation_history.append({"role": role, "content": msg['message_text']})

    transfer_instructions = (
        f"Current user telegram_id is {telegram_id}. "
        "The model must never choose, guess, extract, or override any telegram_id for tool calls. "
        "Always act only for the current authenticated user from server-side request context. "
        "If the user asks for another person's balance or provides another person's telegram ID, refuse and explain that you can only access the current user's own account. "
        "If the user asks for their balance, call check_account_balance. "
        "For money transfers, first collect the receiver account serial ID and the amount if it is missing. "
        "Then call prepare_money_transfer to fetch the receiver name and store the pending transfer. "
        "Show the receiver name back to the user and ask for explicit confirmation. "
        "Only call confirm_money_transfer after the user clearly agrees. "
        "If the user rejects the receiver or wants to stop, call cancel_money_transfer. "
        "Never claim a transfer is completed unless confirm_money_transfer returns success."
        "If a tool result returns 'need_user_name': true, ask the user for their name and then call create_illusion_account with their name. "
        "If a tool result indicates an illusion account was created (contains 'is_illusion': true or mentions testing), inform the user that an illusion account with 2000 YER balance was created for testing purposes. "
        "If confirm_money_transfer returns a result with 'is_illusion': true, make sure to display the testing disclaimer message to the user."
    )
    messages = [{"role": "system", "content": f"{BASE_PROMPT}\n\n{transfer_instructions}"}] + conversation_history + [{"role": "user", "content": user_query}]
    
    
    import asyncio
    loop = asyncio.get_event_loop()
    
    
    def call_hf(msgs):
        return hf_client.chat.completions.create(
            model=MODEL_NAME,
            messages=msgs,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=800
        )

    completion = await loop.run_in_executor(None, lambda: call_hf(messages))
    response_message = completion.choices[0].message

    for _ in range(4):
        if not response_message.tool_calls:
            break

        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            tool_result = await run_tool(tool_call.function.name, args, telegram_id)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        completion = await loop.run_in_executor(None, lambda: call_hf(messages))
        response_message = completion.choices[0].message

    final_response = clean_ai_response(response_message.content if response_message.content else "")

    if db_manager:
        db_manager.save_message(telegram_id, user_query, "user")
        db_manager.save_message(telegram_id, final_response, "assistant")

    return final_response
