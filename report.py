"""AJAN 9: Raporcu. Her gün Telegram'a özet gönderir."""
import os

import requests


class Report:
    def __init__(self):
        self.lines = []

    def add(self, text):
        print(text)
        self.lines.append(text)

    def send(self):
        token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        text = "\n".join(self.lines)
        if not (token and chat):
            print("Telegram ayarlı değil, rapor sadece loga yazıldı.")
            return
        for i in range(0, len(text), 3900):  # Telegram mesaj sınırı
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text[i:i + 3900],
                                "disable_web_page_preview": True}, timeout=30)
