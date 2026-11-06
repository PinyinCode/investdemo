"""
Module quản lý watchlist trên Firestore.
Dùng khi: admin muốn seed watchlist mặc định, backup, hoặc migrate.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    """Khởi tạo Firebase Admin SDK (dùng service account)."""
    if not firebase_admin._apps:
        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if sa_json:
            cred = credentials.Certificate(json.loads(sa_json))
        else:
            cred = credentials.Certificate("service-account.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()


def get_user_watchlist(db, uid: str) -> list:
    doc = db.collection("watchlists").document(uid).get()
    if doc.exists:
        return doc.to_dict().get("symbols", [])
    return []


def set_user_watchlist(db, uid: str, symbols: list, email: str = ""):
    db.collection("watchlists").document(uid).set({
        "symbols": symbols,
        "email": email,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }, merge=True)


def add_symbol_to_watchlist(db, uid: str, symbol: str, email: str = ""):
    symbol = symbol.upper().strip()
    current = get_user_watchlist(db, uid)
    if symbol not in current:
        current.append(symbol)
        set_user_watchlist(db, uid, current, email)
        return True
    return False


def remove_symbol_from_watchlist(db, uid: str, symbol: str, email: str = ""):
    symbol = symbol.upper().strip()
    current = get_user_watchlist(db, uid)
    if symbol in current:
        current.remove(symbol)
        set_user_watchlist(db, uid, current, email)
        return True
    return False


def export_all_watchlists(db, output_file="watchlists_backup.json"):
    data = {}
    for doc in db.collection("watchlists").stream():
        data[doc.id] = doc.to_dict()
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✅ Đã backup {len(data)} watchlists → {output_file}")
    return data


if __name__ == "__main__":
    print("Module watchlist sẵn sàng. Import để dùng.")
