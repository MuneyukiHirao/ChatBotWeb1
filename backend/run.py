#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from datetime import datetime

# chat_bot.py から generate_bot_reply をimport
from chat_bot import generate_bot_reply

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
# app = Flask(__name__, static_folder=..., static_url_path=...)

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "demo-secret-key")
#CORS(app, origins=["https://upgraded-space-cod-6jwrvpw49j6cggr-5000.app.github.dev/", "https://upgraded-space-cod-6jwrvpw49j6cggr-5173.app.github.dev/"])
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

sessions = {}  # sessionId -> { isLoggedIn, userId, conversation (list) }


def get_session_data(session_id):
    if session_id not in sessions:
       debug_print(f"session_id={session_id} not found. Creating new session with isLoggedIn=False.")
       sessions[session_id] = {
            "isLoggedIn": False,
            "userId": None,
            "conversation": []
        }
    return sessions[session_id]

# --------------------------------------
# デバッグ用: コマンドラインにメッセージを出力する
def debug_print(msg):
    print(f"[DEBUG] {msg}", flush=True)  # flush=True で即時出力
# --------------------------------------

@app.route("/api/login", methods=["POST"])
def api_login():
    debug_print("==== /api/login called ====")
    data = request.json
    debug_print(f"POST data: {data}")
    if not data:
        debug_print("No data received in /api/login")
        return jsonify({"error": "No data"}), 400

    user_id = data.get("userId")
    password = data.get("password")
    debug_print(f"user_id={user_id}, password={password}")

    if user_id == "test" and password == "test":
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "isLoggedIn": True,
            "userId": None,
            "conversation": []
        }
        debug_print(f"Login success, sessionId={session_id}")
        return jsonify({"sessionId": session_id}), 200
    else:
        debug_print("Invalid credentials")
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/users", methods=["GET"])
def api_users():
    debug_print("==== /api/users called ====")
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users_data = json.load(f)
    except FileNotFoundError:
        debug_print("users.json not found")
        return jsonify({"users": []})
    except json.JSONDecodeError:
        debug_print("users.json decode error")
        return jsonify({"users": []})

    # 2) customer_machine_list.jsonを読み込み
    machine_list = []
    try:
        with open("customer_machine_list.json", "r", encoding="utf-8") as f:
            machine_list = json.load(f)  # [{ "companyId":"C001","machines":[...] }, ...]
    except FileNotFoundError:
        debug_print("customer_machine_list.json not found")
        # ない場合は空配列 -> 全社0台扱い
    except json.JSONDecodeError:
        debug_print("customer_machine_list.json decode error")

    # machine_listを { "C001":台数, "C002":台数, ... } にまとめる
    company_machine_count = {}
    for company_block in machine_list:
        c_id = company_block["companyId"]
        c_machines = company_block.get("machines", [])
        company_machine_count[c_id] = len(c_machines)

    output_list = []
    for u in users_data:
        c_id = u.get("companyId", "")
        # c_idがmachine_listにあれば、台数を取得。なければ0
        m_count = company_machine_count.get(c_id, 0)
        out_item = {
            "userId": u["userId"],
            "userName": u["userName"],
            "companyId": c_id,
            "companyName": u.get("companyName", ""),
            "machineCount": m_count
        }
        output_list.append(out_item)
    debug_print(f"Returning {len(output_list)} users with machineCount.")
    return jsonify({"users": output_list})


@app.route("/api/select-user", methods=["POST"])
def api_select_user():
    debug_print("==== /api/select-user called ====")
    data = request.json
    debug_print(f"POST data: {data}")
    if not data:
        return jsonify({"error": "No data"}), 400

    session_id = data.get("sessionId")
    chosen_user_id = data.get("userId")
    if not session_id or not chosen_user_id:
        return jsonify({"error": "sessionId and userId required"}), 400

    sess = get_session_data(session_id)
    if not sess["isLoggedIn"]:
        return jsonify({"error": "Not logged in"}), 401

    # users.json を検索して userId=chosen_user_id のユーザ情報を得る
    user_info = find_user_info_by_userId(chosen_user_id)
    sess["userInfo"] = user_info  # {"userId":"U001","userName":"山田太郎","companyName":"ABC建設",...}

    sess["userId"] = chosen_user_id
    sess["conversation"] = []  # reset conversation
    debug_print(f"User {chosen_user_id} selected for session={session_id}")
    return jsonify({"message": f"User {chosen_user_id} selected"}), 200

def find_user_info_by_userId(user_id):
    # users.jsonを読み込み、該当のuser_idを探してreturn
    with open("users.json", "r", encoding="utf-8") as f:
        all_users = json.load(f)
    for u in all_users:
        if u["userId"] == user_id:
            return u
    return {}

# =====================
# ここからが今回のポイント： /api/chat
# =====================
@app.route("/api/chat", methods=["POST"])
def api_chat():
    debug_print("==== /api/chat called ====")
    """
    { "sessionId":..., "message":"...ユーザ入力..." }
    システムプロンプト (system_prompt.txt) + 既存会話履歴 + 今回のユーザメッセージ
    をまとめて generate_bot_reply(conversation) に渡し、回答を得る。
    """
    data = request.json
    debug_print(f"POST data: {data}")

    if not data:
        debug_print("No data in /api/chat")
        return jsonify({"error": "No data"}), 400

    session_id = data.get("sessionId")
    user_msg = data.get("message", "")
    debug_print(f"sessionId={session_id}, user_msg='{user_msg}'")

    if not session_id:
        return jsonify({"error": "sessionId required"}), 400

    sess = get_session_data(session_id)
    if not sess["isLoggedIn"]:
        return jsonify({"error": "Not logged in"}), 401

    # 1) system_prompt.txt の読み込み
    system_prompt_text = ""
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt_text = f.read()
    except FileNotFoundError:
        system_prompt_text = "あなたは建設機械のチャットボットです。"

    # 2) ユーザ情報を追加のシステムメッセージとして注入 (もしあるなら)
    user_info_msg = ""
    user_info = sess.get("userInfo", {})
    if user_info:
        user_info_msg = f"""
        現在のユーザ情報:
          ユーザID: {user_info.get("userId","")}
          氏名: {user_info.get("userName","")}
          会社ID: {user_info.get("companyId","")}
          会社名: {user_info.get("companyName","")}
        
        必要に応じてこれらを回答に活用してください。
        """

    # 2) 会話全体をmessages形式にまとめる
    #   - 先頭: systemプロンプト
    #   - 続き: sess["conversation"] (過去のユーザ/assistant)
    #   - 最後: 今回のユーザメッセージ
    conversation = []
    conversation.append({"role": "system", "content": system_prompt_text})

    if user_info_msg:
        conversation.append({"role":"system", "content": user_info_msg})
        
    # 過去の履歴を追加
    # sess["conversation"] は [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]
    for msg in sess["conversation"]:
        conversation.append(msg)

    # 今回のユーザメッセージを会話に追加
    conversation.append({"role": "user", "content": user_msg})

    # 3) OpenAIに問い合わせ (generate_bot_reply)
    bot_reply = generate_bot_reply(conversation)

    # 4) conversationに最終的な2つのメッセージ(ユーザ→assistant)を反映
    #   - すでに下記のような構造だが、generate_bot_reply 内部で conversation を増やしているかどうかによる
    #   - ここでは回答テキスト(bot_reply)を会話に追記
    sess["conversation"].append({"role": "user", "content": user_msg})
    sess["conversation"].append({"role": "assistant", "content": bot_reply})

    debug_print(f"conversation so far: {sess['conversation']}")

    # 5) 応答を返す
    return jsonify({
        "reply": bot_reply,
        "conversation": sess["conversation"]
    }), 200


@app.route("/api/chat/reset", methods=["POST"])
def api_chat_reset():
    debug_print("==== /api/chat/reset called ====")
    data = request.json
    debug_print(f"POST data: {data}")
    if not data:
        return jsonify({"error": "No data"}), 400

    session_id = data.get("sessionId")
    sess = get_session_data(session_id)
    if not sess["isLoggedIn"]:
        return jsonify({"error": "Not logged in"}), 401

    sess["conversation"] = []
    debug_print(f"Chat reset for session {session_id}")
    return jsonify({"message": "Chat history reset."}), 200


@app.route("/api/chat/finish", methods=["POST"])
def api_chat_finish():
    debug_print("==== /api/chat/finish called ====")
    data = request.json
    debug_print(f"POST data: {data}")

    if not data:
        return jsonify({"error": "No data"}), 400

    session_id = data.get("sessionId")
    if session_id in sessions:
        del sessions[session_id]

    debug_print(f"Chat finished (session {session_id} removed).")
    return jsonify({"message": "Chat finished"}), 200


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_print(f"=== Starting server on 0.0.0.0:{port} ===")
    app.run(host="0.0.0.0", port=port, debug=True)
