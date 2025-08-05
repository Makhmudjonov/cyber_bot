import sys
import threading
from django.apps import AppConfig


class AppsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps'

    def ready(self):
        from threading import Thread
        from apps.bot.cs2form import run_bot
        Thread(target=run_bot, name="TelegramBot", daemon=True).start()