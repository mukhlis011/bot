import os
import time
import base64
import hmac
import hashlib
import requests
from dotenv import load_dotenv

# === Konfigurasi ===
load_dotenv()
API_KEY = os.getenv("KUCOIN_API_KEY")
API_SECRET = os.getenv("KUCOIN_API_SECRET")
API_PASSPHRASE = os.getenv("KUCOIN_API_PASSPHRASE")
BASE_URL = "https://api.kucoin.com"

def kucoin_signature(secret, str_to_sign):
    return base64.b64encode(
        hmac.new(secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()
    ).decode()

def get_auth_headers(method, endpoint, body=""):
    now = str(int(time.time() * 1000))
    str_to_sign = now + method + endpoint + body
    signature = kucoin_signature(API_SECRET, str_to_sign)
    passphrase = kucoin_signature(API_SECRET, API_PASSPHRASE)

    return {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        # coba versi 1 dulu
        "KC-API-KEY-VERSION": "1",
        "Content-Type": "application/json"
    }

def test_kucoin_api():
    if not API_KEY or not API_SECRET or not API_PASSPHRASE:
        print("❌ API Key/Secret/Passphrase tidak ditemukan di .env")
        return

    try:
        # Coba ambil akun saldo (auth)
        print("🔐 Mengirim request saldo ke KuCoin...")
        endpoint = "/api/v1/accounts"
        url = BASE_URL + endpoint
        headers = get_auth_headers("GET", endpoint)
        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            print("✅ API KuCoin BERHASIL! Respon saldo berhasil diterima.")
            data = res.json()
            for acc in data.get("data", []):
                if float(acc["available"]) > 0 or float(acc["holds"]) > 0:
                    print(f"💰 {acc['currency']}: Free={acc['available']}, Locked={acc['holds']}")
        elif res.status_code == 401:
            print("❌ API GAGAL: Unauthorized. Periksa API Key, Secret, atau Passphrase.")
        else:
            print(f"⚠️ Respon tidak diharapkan: {res.status_code} - {res.text}")

    except Exception as e:
        print(f"🚨 ERROR: {e}")

if __name__ == "__main__":
    test_kucoin_api()
