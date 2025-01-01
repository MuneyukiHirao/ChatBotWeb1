#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os

BASE_URL = "http://localhost:5000"  # Flaskが起動中のURL:PORTを指定

def main():
    print("=== バックエンドAPIテスト開始 ===")
#    print(os.environ.get("OPENAI_API_KEY"))

    # 1) ログイン (POST /api/login)
    print("\n[1] ログイン試験")
    login_data = {
        "userId": "test",
        "password": "test"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if r.status_code == 200:
        login_json = r.json()
        session_id = login_json.get("sessionId")
        print(f"  成功: sessionId = {session_id}")
    else:
        print(f"  失敗: status_code={r.status_code}, text={r.text}")
        return  # テスト継続不可

    # 2) ユーザ一覧取得 (GET /api/users)
    print("\n[2] ユーザ一覧取得")
    r2 = requests.get(f"{BASE_URL}/api/users")
    if r2.status_code == 200:
        users_json = r2.json()
        print(f"  ユーザ一覧取得成功: {json.dumps(users_json, ensure_ascii=False, indent=2)}")
    else:
        print(f"  失敗: status_code={r2.status_code}, text={r2.text}")

    # 3) ユーザ選択 (POST /api/select-user)
    print("\n[3] ユーザ選択")
    # ここではテストとして "U001" を選ぶ例:
    select_data = {
        "sessionId": session_id,
        "userId": "U001"
    }
    r3 = requests.post(f"{BASE_URL}/api/select-user", json=select_data)
    if r3.status_code == 200:
        print("  ユーザ選択成功:", r3.json())
    else:
        print(f"  失敗: status_code={r3.status_code}, text={r3.text}")

    # 4) チャット送信 (POST /api/chat)
    print("\n[4] チャット送信")
    chat_data = {
        "sessionId": session_id,
        "message": "PC200-8の500001のエンジン重量を教えて"
    }
    r4 = requests.post(f"{BASE_URL}/api/chat", json=chat_data)
    if r4.status_code == 200:
        chat_json = r4.json()
        print("  チャット応答:", chat_json.get("reply"))
        print("  会話履歴:", chat_json.get("conversation"))
    else:
        print(f"  失敗: status_code={r4.status_code}, text={r4.text}")

    # 5) チャットリセット (POST /api/chat/reset)
    print("\n[5] チャットリセット")
    reset_data = {"sessionId": session_id}
    r5 = requests.post(f"{BASE_URL}/api/chat/reset", json=reset_data)
    if r5.status_code == 200:
        print("  リセット成功:", r5.json())
    else:
        print(f"  失敗: status_code={r5.status_code}, text={r5.text}")

    # 6) チャット終了 (POST /api/chat/finish)
    print("\n[6] チャット終了")
    finish_data = {"sessionId": session_id}
    r6 = requests.post(f"{BASE_URL}/api/chat/finish", json=finish_data)
    if r6.status_code == 200:
        print("  チャット終了:", r6.json())
    else:
        print(f"  失敗: status_code={r6.status_code}, text={r6.text}")

    print("\n=== バックエンドAPIテスト完了 ===")


if __name__ == "__main__":
    main()
