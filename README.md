# Hadhramout Bank Customer Service Assistant

An intelligent customer service assistant that helps bank customers get instant support, check account-related information, and complete guided money transfers through a secure and conversational experience.

## Project Preview

<p align="center">
  <img src="media/customer_service.png" alt="Project Logo" width="600">
</p>


## What This Project Does

This project acts as a digital banking support agent that responds to customer questions in a natural way while following banking rules and service policies. It is designed to reduce support load, speed up routine requests, and improve customer experience with clear step-by-step guidance.

It supports both real customer scenarios and safe testing scenarios. This allows teams to validate service behavior, test transfer conversations, and train operations without affecting real balances.

## Key Capabilities

- **Conversational Customer Support** - Handles common banking questions with clear, context-aware replies
- **Guided Money Transfers** - Walks customers through transfer steps with validation and confirmation
- **Customer Session Memory** - Uses recent conversation context to keep replies relevant and consistent
- **Test-Safe Account Mode** - Supports controlled demo/testing flows with isolated account behavior
- **Audit-Friendly Records** - Maintains transfer and conversation history for tracking and review
- **Policy-Aligned Responses** - Follows predefined banking instructions and communication style

## Who This Is For

- **Bank Customers** - Get quick answers and guided help for common banking requests
- **Customer Support Teams** - Reduce repetitive workload and focus on complex customer issues
- **Operations Teams** - Monitor service quality and validate transfer workflows safely
- **Product and Service Managers** - Improve support quality using measurable performance indicators

## Success Metrics

- **First Response Time** - How quickly customers receive the first useful reply
- **Transfer Completion Rate** - Percentage of initiated transfers that complete successfully
- **Support Deflection Rate** - Percentage of requests resolved without manual agent intervention
- **Customer Clarity Score** - Quality of customer understanding after each interaction
- **Error and Escalation Rate** - Frequency of failed actions and handoffs to human support

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project URL
- Pinecone account and API key
- Hugging Face API token
- Telegram Bot token

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd customer_service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with the following variables:
   ```env
   # Database
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   
   # Vector Search
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX=customerserviceindex
   
   # AI Model
   HF_TOKEN=your_huggingface_token
   HF_MODEL=dphn/Dolphin-Mistral-24B-Venice-Edition
   PROMPT=You are a helpful banking customer service assistant.
   TRANSFER_PROMPT=Current user telegram_id is {telegram_id}. The model must never choose, guess, extract, or override any telegram_id for tool calls.
   
   # Telegram
   TELEGRAM_TOKEN=your_telegram_bot_token
   TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
   TELEGRAM_DOMAIN=https://api.telegram.org
   ```

## 🔧 Hugging Face Spaces Configuration

When deploying to Hugging Face Spaces, set these variables in the Space "Secrets" or settings panel rather than committing them to source control:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX` (default: `customerserviceindex`)
- `HF_TOKEN` or `HF_API_KEY`
- `HF_MODEL` (optional)
- `PROMPT` (optional)
- `TRANSFER_PROMPT` (optional)
- `TELEGRAM_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_DOMAIN` (optional, default: `https://api.telegram.org`)

Use `TRANSFER_PROMPT` when you need to customize transfer behavior. It must include `{telegram_id}` so the system can safely bind the request to the current authenticated user.
 
**PROMPT vs TRANSFER_PROMPT**

- `PROMPT`: General system prompt that sets the assistant's persona, tone, and default behavior for all user interactions.
- `TRANSFER_PROMPT`: A focused, security-sensitive prompt that contains strict rules and step-by-step procedures for money transfers (e.g., collect receiver serial ID and amount, call `prepare_money_transfer` / `confirm_money_transfer` / `cancel_money_transfer`, never guess or override the `telegram_id`, and handle illusion/test accounts).

Why keep both:
- **Separation of concerns**: Update transfer policies without changing general assistant behavior.
- **Safety & compliance**: Transfer flows require auditable, strict instructions that shouldn't be mixed with everyday conversational rules.
- **Operational flexibility**: Configure `TRANSFER_PROMPT` via environment/Space secrets to change transfer policies quickly in production.
- **Reduced risk**: A dedicated transfer prompt lowers the chance of accidental or unsafe tool calls during financial operations.

## 🏃‍♂️ Running the Application

1. **Start the development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Set up Telegram webhook** (optional)
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_WEBHOOK_URL>&secret_token=<YOUR_SECRET_TOKEN>"
   ```

## 📡 API Endpoints

### Core Endpoints
- `GET /` - Health check and server status
- `POST /webhook` - Telegram webhook endpoint
- `POST /test` - Test webhook functionality
- `GET /dns-test` - DNS connectivity test
- `POST /ai-test` - AI response testing endpoint

### Testing Endpoints
- `POST /ai-test` - Test AI responses directly
  ```bash
  curl -X POST http://localhost:8000/ai-test \
    -H "Content-Type: application/json" \
    -H "X-Telegram-Bot-Api-Secret-Token: your-secret" \
    -d '{"message":"check my balance","telegram_id":12345}'
  ```

## 🧪 Testing the System

### 1. Test with Real Account
Use existing telegram_id from `transfers/mock_bank_accounts.json`:
- 12 (Test Sender) - Balance: 1900 YER
- 991001 (Ahmed Salem) - Balance: 1990 YER
- 991002 (Mona Ali) - Balance: 800 YER

### 2. Test with Illusion Account
Use any telegram_id not in the system:
- System will ask for user name
- Creates illusion account with 2000 YER balance
- Shows testing disclaimer after transfers

### 3. Money Transfer Testing
```bash
# Start a transfer
curl -X POST http://localhost:8000/ai-test \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your-secret" \
  -d '{"message":"transfer 100 YER to account 2001","telegram_id":12345}'
```

## 🏗️ Project Structure

```
customer_service/
├── main.py                 # FastAPI application entry point
├── ai_service.py          # AI response handling and tools
├── database.py            # Supabase database operations
├── utils.py               # Utility functions
├── transfers/             # Money transfer system
│   ├── service.py         # Core transfer logic
│   ├── __init__.py        # Transfer module exports
│   └── mock_bank_accounts.json  # Mock account data
├── config.py              # Configuration and environment variables
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Transfer System Features
- **Real Accounts**: Marked with `"is_real": true` in JSON
- **Illusion Accounts**: Marked with `"is_real": false`, created for testing
- **Account Creation**: Automatic illusion account creation with user name requirement
- **Transfer Validation**: Balance checks, duplicate prevention, confirmation flow
- **Testing Disclaimers**: Clear messages for illusion account transactions

### AI Tools Available
- `search_bank_knowledge` - Search banking knowledge base
- `check_account_balance` - Get user account balance
- `prepare_money_transfer` - Initiate transfer process
- `confirm_money_transfer` - Complete pending transfer
- `cancel_money_transfer` - Cancel pending transfer
- `create_illusion_account` - Create test account

## 🚀 Deployment

### Hugging Face Spaces
The application is configured for deployment on Hugging Face Spaces using Docker. The `README.md` at the root contains the Spaces configuration.

### Local Development
For local development, ensure all environment variables are set and run with:
```bash
uvicorn main:app --reload
```

## 📝 Notes

- All illusion accounts are prefixed with "Test User" in the name
- Real accounts require physical bank visits for creation
- Transfer amounts are validated against available balance
- All transactions are logged with timestamps and unique IDs
- The system automatically handles both real and illusion account scenarios

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the **Apache License 2.0**.

## Local Development
```bash
docker build -t customer-service .
docker run -p 8000:8000 customer-service
```
