# api_functions.py
import requests
import json
import os
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv



# ==========================
# 1) ヘルパー関数：JSON読込
# ==========================
def load_json_file(file_path: str):
    """指定された JSON ファイルを読み込み、Pythonオブジェクトとして返す。
       ファイルが存在しない場合は、空のリストを返す。
    """
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================
# 2) ヘルパー関数：JSON書き込み
# ==============================
def save_json_file(file_path: str, data):
    """Pythonオブジェクトを JSON ファイルに書き込む。"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====================================================
# 3) getMachineInfo: customer_machine_list.json の検索
# ====================================================
def getMachineInfo(model: str, serial: str) -> List[Dict]:
    """
    指定したmodel, serialに該当する車両を探す。
    customer_machine_list.jsonを読み込み、複数該当がある場合はすべて返す。
    戻り値は以下の形式のリスト（複数要素がある可能性もある）。
        [
          {
            "latitude": float,
            "longitude": float,
            "address": str,
            "customerName": str,
            "customerId": str,
            "machineId": str,
            "dealerCode": str,
            "dealerName": str,
            "contactPersonId": str,
            "contactPersonName": str
          },
          ...
        ]
    ※ 今回のサンプルでは、緯度・経度など仮データを適当に埋めています。
    """
    # JSONからデータ読込
    machine_list = load_json_file("customer_machine_list.json")

    # 結果用リスト
    results = []

    # 今回は dealerCode, dealerName, contactPersonId, contactPersonName 等の情報は
    # サンプルとして固定値やダミーを入れる。
    # address も「顧客IDに応じた適当な住所」を仮定とする。
    dummy_addresses = {
        "C001": "東京都品川区XXX",
        "C002": "神奈川県横浜市XXX",
        "C003": "埼玉県さいたま市XXX",
        "C004": "千葉県千葉市XXX",
        "C005": "茨城県水戸市XXX"
    }

    for company_data in machine_list:
        company_id = company_data["companyId"]
        for mach in company_data["machines"]:
            if mach["model"] == model and mach["serial"] == serial:
                # ダミー情報をセット
                item = {
                    "latitude": 35.0,       # ダミー
                    "longitude": 139.0,     # ダミー
                    "address": dummy_addresses.get(company_id, "所在地不明"),
                    "customerName": "不明", # 後で users.json と突合するなら実装してもOK
                    "customerId": company_id,
                    "machineId": mach["machineId"],
                    "dealerCode": "D001",   # ダミー
                    "dealerName": "Sample Dealer",
                    "contactPersonId": "S999",      # ダミー
                    "contactPersonName": "Contact Person Dummy"
                }
                results.append(item)

    if not results:
        return { "found": False, "message": "No such machine in the list" }
    else:
        return { "found": True, "data": results }



# =====================================================================
# 5) notifyStaff: スタッフにメッセージを通知し、JSONファイルに追記する
# =====================================================================
def notifyStaff(userId: str,
                title: str,
                messageContent: str,
                customerId: str,
                customerName: str,
                customerUserId: str,
                customerUserName: str,
                recipientUserIds: List[str]) -> Dict:
    """
    担当者(複数)に対して通知を行う想定。
    - staff_inbox_{staffId}.json というファイルを用意し、メッセージを追記していく。
    - 成功/失敗のみを返すシンプルな設計。
    """
    now_str = datetime.utcnow().isoformat()

    for staff_id in recipientUserIds:
        # ファイル名: staff_inbox_S001.json のように
        inbox_filename = f"staff_inbox_{staff_id}.json"

        # すでにファイルがあれば読み込み、なければ空リスト
        current_inbox = load_json_file(inbox_filename)

        # 新しいメッセージアイテム
        new_message = {
            "timestamp": now_str,
            "title": title,
            "messageContent": messageContent,
            "customerId": customerId,
            "customerName": customerName,
            "customerUserId": customerUserId,
            "customerUserName": customerUserName,
            "fromUserId": userId
        }
        current_inbox.append(new_message)

        # ファイルに書き戻し
        save_json_file(inbox_filename, current_inbox)

    return {
        "success": True,
        "errorMessage": ""
    }

SUBSCRIPTION_KEY = "3da1878c519c497182eb50578a3eaeed"
SEARCH_API_URL = "https://aibot-apim-uat-jpe.azure-api.net/satori-uat/DocumentQueryWithAnswer"

def searchManual(model: str, serial: str, documentType: str, query: str):
    """
    取扱説明書 or ショップマニュアルを検索する本実装。
    """
    if documentType in ["取扱説明書", "取説", "operation manual (jpn)"]:
        documentType = "Operation and maintenance manual"
    elif documentType in ["ショップマニュアル", "分解組立手順", "shop manual (jpn)"]:
        documentType = "Shop Manual"

    url = "https://aibot-apim-uat-jpe.azure-api.net/satori-uat/DocumentQueryWithAnswer"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": "3da1878c519c497182eb50578a3eaeed"
    }
    body = {
        "Query": query,
        "DocumentNumber": "SEN06519-24",
        "Source": "Document Center",
        "DocumentType": documentType,
        "Language": "English"
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        topN = data.get("topNResults", {})
        openAiAnswer = topN.get("openAiAnswer", "")

        return {
            "openAiAnswer": openAiAnswer,
            "raw": data
        }

    except requests.RequestException as e:
        return {
            "openAiAnswer": "",
            "error": str(e)
        }
