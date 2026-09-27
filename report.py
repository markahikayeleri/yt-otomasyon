"""AJAN 9: Raporcu. Raporu GitHub'a (e-posta bildirimi) ve varsa Telegram'a gönderir."""
import os

import requests


class Report:
    def __init__(self):
        self.lines = []

    def add(self, text):
        print(text)
        self.lines.append(text)

    def send(self):
        text = "\n\n".join(self.lines)
        os.makedirs("output", exist_ok=True)
        with open("output/report.md", "w", encoding="utf-8") as f:
            f.write(text)
        token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        if not (token and chat):
            return
        for i in range(0, len(text), 3900):
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text[i:i + 3900],
                                "disable_web_page_preview": True}, timeout=30)
