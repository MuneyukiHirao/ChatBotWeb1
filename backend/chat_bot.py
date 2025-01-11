#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import openai
from typing import List, Dict

# debug用フラグ (必要に応じて切替)
DEBUG = True

# api_functions.pyに定義した関数をimportする想定
from api_functions import getMachineInfo, searchManual, notifyStaff


function_definitions = [
    {
        "name": "getMachineInfo",
        "description": "車両情報を取得する",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "serial": {"type": "string"}
            },
            "required": ["model", "serial"]
        }
    },
    {
        "name": "searchManual",
        "description": "マニュアルを検索する('Operation and maintenance manual' or 'Shop manual')。",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "serial": {"type": "string"},
                "documentType": {"type": "string"},
                "query": {"type": "string"}
            },
            "required": ["model", "serial", "documentType", "query"]
        }
    },
    {
        "name": "notifyStaff",
        "description": "担当者にメッセージを通知する",
        "parameters": {
            "type": "object",
            "properties": {
                "userId": {"type": "string"},
                "title": {"type": "string"},
                "messageContent": {"type": "string"},
                "customerId": {"type": "string"},
                "customerName": {"type": "string"},
                "customerUserId": {"type": "string"},
                "customerUserName": {"type": "string"},
                "recipientUserIds": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [
                "userId", "title", "messageContent", "customerId",
                "customerName", "customerUserId", "customerUserName",
                "recipientUserIds"
            ]
        }
    }
]


def generate_bot_reply(conversation: List[Dict]) -> str:
    """
    会話履歴( conversation )をOpenAIに渡し、Function calling対応で応答を受け取る。
    もしfunction_callが返ってきたら、対応する関数を呼び出して結果を再度LLMに渡し、
    最終テキストを得る。
    """
    openai.api_key = os.environ.get("OPENAI_API_KEY", "")
    if DEBUG:
        print("=== [DEBUG] generate_bot_reply ===")
        # 省略: debug出力
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=conversation,
            functions=function_definitions,
            function_call="auto",
            temperature=0.7
        )
    except Exception as e:
        if DEBUG:
            print("[DEBUG] OpenAI API call exception:", str(e))
        return f"[OpenAI API Error] {str(e)}"

    if not response.choices:
        if DEBUG:
            print("[DEBUG] No choices returned from OpenAI")
        return "[Error] No response from OpenAI"

    response_message = response.choices[0].message
    if response_message is None:
        if DEBUG:
            print("[DEBUG] response_message is None")
        return "[Error] response_message is None"

    # function_call チェック
    if hasattr(response_message, "function_call") and response_message.function_call is not None:
        fn_name = response_message.function_call.name
        fn_args_str = response_message.function_call.arguments
        try:
            fn_args = json.loads(fn_args_str)
        except json.JSONDecodeError as ex:
            if DEBUG:
                print("[DEBUG] JSONDecodeError in function_call arguments:", str(ex))
            fn_args = {}

        # 関数を実行
        result_content = handle_function_call(fn_name, fn_args)

        # conversation に function role を追加
        conversation.append({
            "role": "function",
            "name": fn_name,
            "content": json.dumps(result_content, ensure_ascii=False)
        })

        # ===== 二度目の呼び出し (function結果をLLMに再度渡す) =====
        try:
            response2 = openai.chat.completions.create(
                model="gpt-4o",
                messages=conversation,
                functions=function_definitions,
                function_call="auto",
                temperature=0.7
            )
        except Exception as e:
            if DEBUG:
                print("[DEBUG] Second OpenAI API call exception:", str(e))
            return f"[OpenAI API Error] {str(e)}"

        if not response2.choices:
            if DEBUG:
                print("[DEBUG] No choices returned in second call")
            return "[Error] No second response from OpenAI"

        final_msg = response2.choices[0].message

        # ▼▼ リトライ機構 ▼▼
        if (final_msg is None) or (not final_msg.content):
            if DEBUG:
                print("[DEBUG] final message is None or content is empty => RETRY ONCE")
            # リトライしてみる
            try:
                response2_retry = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation,
                    functions=function_definitions,
                    function_call="auto",
                    temperature=0.7
                )
                if not response2_retry.choices:
                    if DEBUG:
                        print("[DEBUG] No choices after RETRY second call")
                    return "[Error] No second response from OpenAI (retry)"

                final_msg_retry = response2_retry.choices[0].message
                if final_msg_retry and final_msg_retry.content:
                    if DEBUG:
                        print("[DEBUG] Retry succeeded => final_msg obtained.")
                    return final_msg_retry.content.strip()
                else:
                    if DEBUG:
                        print("[DEBUG] Retry also returned None or empty content.")
                    return "[Error] Final message is None (retry also failed)"
            except Exception as ee:
                if DEBUG:
                    print("[DEBUG] Second call RETRY exception:", str(ee))
                return f"[OpenAI API Error] {str(ee)}"
        # ▲▲ リトライ機構ここまで ▲▲

        if DEBUG and final_msg.content:
            print("[DEBUG] final text response =>", final_msg.content[:80])

        if final_msg is None or final_msg.content is None:
            if DEBUG:
                print("[DEBUG] final message is STILL None or content is None after no retry or single attempt")
            return "[Error] Final message is None"

        return final_msg.content.strip()

    else:
        # 通常テキスト応答
        bot_reply = response_message.content
        if DEBUG:
            print("[DEBUG] Normal text response =>", bot_reply[:80])
        if not bot_reply:
            return "[Empty response]"
        return bot_reply.strip()



def handle_function_call(fn_name: str, fn_args: dict) -> dict:
    if DEBUG:
        print(f"[DEBUG] function_call: {fn_name} with args={fn_args}")

    if fn_name == "getMachineInfo":
        model = fn_args.get("model", "")
        serial = fn_args.get("serial", "")
        results = getMachineInfo(model, serial)
        return {
            "success": True,
            "data": results
        }
    elif fn_name == "searchManual":
        model = fn_args.get("model", "")
        serial = fn_args.get("serial", "")
        document_type = fn_args.get("documentType", "")
        query = fn_args.get("query", "")
        results = searchManual(model, serial, document_type, query)
        return {
            "success": True,
            "data": results
        }
    elif fn_name == "notifyStaff":
        resp = notifyStaff(**fn_args)
        return {
            "success": resp.get("success", False),
            "errorMessage": resp.get("errorMessage", "")
        }
    else:
        return {
            "success": False,
            "error": f"Function '{fn_name}' is not implemented."
        }


if __name__ == "__main__":
    # 簡単なテスト
    os.environ["OPENAI_API_KEY"] = "sk-xxx"  # debug用に直書き; 普段は.env or Azure Settings
    conv = [
        {"role": "system", "content": "テスト用のシステムプロンプト"},
        {"role": "user", "content": "PC200-8の500001のエンジン重量は？"}
    ]
    reply = generate_bot_reply(conv)
    print("Bot reply:", reply)
