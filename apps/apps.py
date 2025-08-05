import asyncio
import sys
import threading
from django.apps import AppConfig


class AppsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps'

    def ready(self):
        from apps.bot.cs2form import run_bot

        def run():
            asyncio.run(run_bot())

        # Faqat bitta marta ishga tushishi uchun
        if not hasattr(self, 'bot_thread_started'):
            self.bot_thread_started = True
            threading.Thread(target=run, name="TelegramBot", daemon=True).start()