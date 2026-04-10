import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


DATA_FILE = Path(__file__).with_name("mock_bank_accounts.json")
PENDING_FILE = Path(__file__).with_name("pending_transfers.json")
_LOCK = Lock()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=True, indent=2)


def _load_bank_data() -> Dict[str, Any]:
    return _read_json(DATA_FILE, {"accounts": [], "transactions": []})


def _save_bank_data(data: Dict[str, Any]) -> None:
    _write_json(DATA_FILE, data)


def _load_pending_transfers() -> Dict[str, Any]:
    return _read_json(PENDING_FILE, {})


def _save_pending_transfers(data: Dict[str, Any]) -> None:
    _write_json(PENDING_FILE, data)


def _find_account_by_telegram_id(accounts: list[Dict[str, Any]], telegram_id: int) -> Optional[Dict[str, Any]]:
    return next((account for account in accounts if account.get("telegram_id") == telegram_id), None)


def _find_account_by_serial_id(accounts: list[Dict[str, Any]], serial_id: str) -> Optional[Dict[str, Any]]:
    normalized_id = str(serial_id).strip()
    return next((account for account in accounts if str(account.get("serial_id")) == normalized_id), None)


def get_sender_account(telegram_id: int) -> Dict[str, Any]:
    with _LOCK:
        data = _load_bank_data()
        sender = _find_account_by_telegram_id(data["accounts"], telegram_id)
        if sender:
            return {
                "success": True,
                "account": sender,
            }

        return {
            "success": False,
            "message": "You do not have an account in the bank system. Please visit the bank to create an account first.",
        }


def get_account_balance(telegram_id: int) -> Dict[str, Any]:
    sender_result = get_sender_account(telegram_id)
    if not sender_result["success"]:
        return sender_result

    account = sender_result["account"]
    return {
        "success": True,
        "telegram_id": telegram_id,
        "account_id": account["account_id"],
        "serial_id": account["serial_id"],
        "name": account["name"],
        "balance": account.get("balance", 0.0),
        "currency": account.get("currency", "YER"),
    }


def get_receiver_account_name(receiver_serial_id: str) -> Dict[str, Any]:
    with _LOCK:
        data = _load_bank_data()
        receiver = _find_account_by_serial_id(data["accounts"], receiver_serial_id)

        if not receiver:
            return {
                "success": False,
                "message": f"No account was found for ID {receiver_serial_id}.",
            }

        return {
            "success": True,
            "serial_id": receiver["serial_id"],
            "name": receiver["name"],
            "account_id": receiver["account_id"],
            "currency": receiver.get("currency", "YER"),
        }


def prepare_transfer(telegram_id: int, receiver_serial_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
    with _LOCK:
        data = _load_bank_data()
        sender = _find_account_by_telegram_id(data["accounts"], telegram_id)
        if not sender:
            return {
                "success": False,
                "message": "You do not have an account in the bank system. Please visit the bank to create an account first.",
            }

        receiver = _find_account_by_serial_id(data["accounts"], receiver_serial_id)
        if not receiver:
            return {
                "success": False,
                "message": f"No account was found for ID {receiver_serial_id}.",
            }

        if receiver["serial_id"] == sender["serial_id"]:
            return {
                "success": False,
                "message": "You cannot transfer money to the same account.",
            }

        pending_transfers = _load_pending_transfers()
        pending_payload = {
            "telegram_id": telegram_id,
            "sender_name": sender["name"],
            "sender_serial_id": sender["serial_id"],
            "receiver_name": receiver["name"],
            "receiver_serial_id": receiver["serial_id"],
            "receiver_account_id": receiver["account_id"],
            "amount": amount,
            "currency": sender.get("currency", "YER"),
            "created_at": datetime.utcnow().isoformat(),
        }
        pending_transfers[str(telegram_id)] = pending_payload
        _save_pending_transfers(pending_transfers)

        return {
            "success": True,
            "pending_transfer": pending_payload,
            "message": f"Receiver found: {receiver['name']}. Waiting for user confirmation.",
        }


def get_pending_transfer(telegram_id: int) -> Dict[str, Any]:
    with _LOCK:
        pending_transfers = _load_pending_transfers()
        pending_transfer = pending_transfers.get(str(telegram_id))

        if not pending_transfer:
            return {
                "success": False,
                "message": "No pending transfer was found for this Telegram user.",
            }

        return {
            "success": True,
            "pending_transfer": pending_transfer,
        }


def confirm_transfer(telegram_id: int) -> Dict[str, Any]:
    with _LOCK:
        data = _load_bank_data()
        pending_transfers = _load_pending_transfers()
        pending_transfer = pending_transfers.get(str(telegram_id))

        if not pending_transfer:
            return {
                "success": False,
                "message": "There is no pending transfer to confirm.",
            }

        sender = _find_account_by_telegram_id(data["accounts"], telegram_id)
        receiver = _find_account_by_serial_id(data["accounts"], pending_transfer["receiver_serial_id"])

        if not sender or not receiver:
            return {
                "success": False,
                "message": "The sender or receiver account could not be found.",
            }

        amount = pending_transfer.get("amount")
        if amount is None:
            return {
                "success": False,
                "message": "The transfer amount is missing. Ask the user for the amount before confirming.",
            }

        try:
            amount_value = float(amount)
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "The transfer amount is invalid.",
            }

        if amount_value <= 0:
            return {
                "success": False,
                "message": "The transfer amount must be greater than zero.",
            }

        if float(sender.get("balance", 0.0)) < amount_value:
            return {
                "success": False,
                "message": f"Insufficient balance. Available balance is {sender.get('balance', 0.0):.2f} {sender.get('currency', 'YER')}.",
            }

        sender["balance"] = round(float(sender["balance"]) - amount_value, 2)
        receiver["balance"] = round(float(receiver.get("balance", 0.0)) + amount_value, 2)

        transaction = {
            "transaction_id": f"TX-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "telegram_id": telegram_id,
            "sender_serial_id": sender["serial_id"],
            "receiver_serial_id": receiver["serial_id"],
            "receiver_name": receiver["name"],
            "amount": amount_value,
            "currency": sender.get("currency", "YER"),
            "created_at": datetime.utcnow().isoformat(),
        }
        data.setdefault("transactions", []).append(transaction)
        _save_bank_data(data)

        pending_transfers.pop(str(telegram_id), None)
        _save_pending_transfers(pending_transfers)

        return {
            "success": True,
            "transaction": transaction,
            "sender_balance": sender["balance"],
            "message": f"Transfer completed successfully to {receiver['name']}.",
        }


def cancel_transfer(telegram_id: int) -> Dict[str, Any]:
    with _LOCK:
        pending_transfers = _load_pending_transfers()
        removed = pending_transfers.pop(str(telegram_id), None)
        _save_pending_transfers(pending_transfers)

        if not removed:
            return {
                "success": False,
                "message": "There is no pending transfer to cancel.",
            }

        return {
            "success": True,
            "message": "The pending transfer has been canceled.",
        }

