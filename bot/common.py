import os
import asyncio
import traceback
import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import aiomysql

SERVICE_NAME = "FRIDAY"
TOKEN = os.getenv("TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID"))
TARGET_URL = "https://marvel.disney.co.jp/news"
