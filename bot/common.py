import asyncio
import logging
import os
import traceback
import aiohttp
import aiomysql
from bs4 import BeautifulSoup
import discord
from discord.ext import commands

SERVICE_NAME = "FRIDAY"
TOKEN = os.getenv("TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID"))
TARGET_URL = "https://marvel.disney.co.jp/news"

# ログの設定
format = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{",
)
handler = logging.StreamHandler()
handler.setFormatter(format)
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
bot_logger = logging.getLogger(SERVICE_NAME)


async def write_log_message(message: str, category: str):
    if category == "INFO":
        bot_logger.info(message)
    elif category == "ERROR":
        bot_logger.error(message)
    else:
        bot_logger.warning(message)
