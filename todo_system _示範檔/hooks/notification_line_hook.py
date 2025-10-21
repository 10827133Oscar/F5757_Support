#!/usr/bin/env python3
"""
Claude Code Notification Hook - LINE 推播通知
當 Claude Code 發送通知時，將訊息轉發到 LINE
"""

import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import requests


def send_line_notification(message: str, access_token: str, user_id: str) -> bool:
    """
    發送 LINE 推播訊息

    Args:
        message: 要發送的訊息內容
        access_token: LINE Channel Access Token
        user_id: 接收訊息的 LINE User ID

    Returns:
        bool: 發送成功返回 True，失敗返回 False
    """
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE 推播失敗: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return False


def main():
    """主程式入口"""
    try:
        # 讀取從 stdin 傳入的 JSON 資料
        input_data = sys.stdin.read()

        if not input_data.strip():
            print("⚠️  未收到輸入資料", file=sys.stderr)
            sys.exit(1)

        # 解析 JSON
        try:
            event_data = json.loads(input_data)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失敗: {e}", file=sys.stderr)
            sys.exit(1)

        # 檢查是否為 Notification 相關事件
        # 支援多種通知類型: Notification, IdleNotification 等
        hook_event_name = event_data.get("hook_event_name")

        # 記錄收到的事件類型（用於除錯）
        print(f"📥 收到事件: {hook_event_name}", file=sys.stderr)

        # 只處理包含 "Notification" 的事件
        if not hook_event_name or "Notification" not in hook_event_name:
            # 不是通知事件，靜默退出
            sys.exit(0)

        # 取得通知訊息
        notification_message = event_data.get("message")
        if not notification_message:
            print("⚠️  通知訊息為空", file=sys.stderr)
            sys.exit(1)

        # 載入環境變數
        # 從當前檔案位置往上找到專案根目錄的 .env
        current_dir = Path(__file__).parent.parent
        env_path = current_dir / ".env"

        if not env_path.exists():
            print(f"❌ 找不到 .env 檔案: {env_path}", file=sys.stderr)
            print("請建立 .env 檔案並設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID", file=sys.stderr)
            sys.exit(1)

        load_dotenv(env_path)

        # 讀取 LINE 設定
        access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        user_id = os.getenv("LINE_USER_ID")

        if not access_token or access_token == "your_channel_access_token_here":
            print("❌ 請在 .env 檔案中設定 LINE_CHANNEL_ACCESS_TOKEN", file=sys.stderr)
            sys.exit(1)

        if not user_id or user_id == "your_line_user_id_here":
            print("❌ 請在 .env 檔案中設定 LINE_USER_ID", file=sys.stderr)
            sys.exit(1)

        # 格式化訊息 - 添加來源標示
        formatted_message = f"🤖 Claude Code 通知\n\n{notification_message}"

        # 發送 LINE 推播
        success = send_line_notification(formatted_message, access_token, user_id)

        if success:
            print(f"✅ LINE 推播已發送")
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
