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
intent = discord.Intents.default()
intent.message_content = True
client = commands.Bot(command_prefix="-", intents=intent)
task = None


# MySQLの接続設定
class UseMySQL:
    pool: aiomysql.Pool | None = None

    @classmethod
    async def init_pool(cls):
        if cls.pool is None:
            cls.pool = await aiomysql.create_pool(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                db=os.getenv("DB_NAME"),
                autocommit=True,
                minsize=1,
                maxsize=5,
            )

    @classmethod
    async def close_pool(cls):
        if cls.pool:
            cls.pool.close()
            await cls.pool.wait_closed()
            cls.pool = None

    @classmethod
    async def run_sql(cls, sql: str, params: tuple = ()) -> list | None:
        async with cls.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                if sql.strip().upper().startswith("SELECT"):
                    rows = await cur.fetchall()
                    return [r[0] if isinstance(r, tuple) else r for r in rows]


class Crawler:
    session: aiohttp.ClientSession | None = None

    @classmethod
    async def init_session(cls):
        if cls.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            cls.session = aiohttp.ClientSession(timeout=timeout)

    @classmethod
    async def close_session(cls):
        if cls.session:
            await cls.session.close()
            cls.session = None

    @classmethod
    async def get_soup(cls, url: str) -> BeautifulSoup | str:
        try:
            await asyncio.sleep(1)
            async with cls.session.get(url) as resp:
                if resp.status != 200:
                    return "ERROR"
                text = await resp.text()
                return BeautifulSoup(text, "html.parser")
        except Exception:
            return "ERROR"

    @classmethod
    async def try_to_get_soup(cls, url: str, retries: int = 5) -> BeautifulSoup | str:
        for _ in range(retries):
            soup = await cls.get_soup(url)
            if soup != "ERROR":
                return soup
        return "FAILED"

    @staticmethod
    async def register_crawl(target_url: str, method: str):
        await UseMySQL.run_sql(
            "INSERT INTO crawls (target_url, method, service) VALUES (%s, %s, %s)",
            (target_url, method, SERVICE_NAME),
        )

    @classmethod
    async def get_new_articles(cls) -> list | str:
        try:
            soup = await cls.try_to_get_soup(TARGET_URL)
            if soup == "FAILED":
                return "ERROR"
            await cls.register_crawl(TARGET_URL, "HTTP_GET")
            targets = soup.find_all("div", class_="text-content")
            new_articles = []
            for target in targets:
                new_articles.append(target.find("a").get("href"))
            return new_articles
        except Exception as e:
            print(e)
            return "ERROR"

    @classmethod
    async def get_article_title(cls, url: str) -> str:
        try:
            soup = await cls.try_to_get_soup(url)
            if soup == "FAILED":
                return "ERROR"
            await cls.register_crawl(url, "HTTP_GET")
            title = soup.find("title").text.strip()
            return title
        except Exception as e:
            print(e)
            return "ERROR"


async def send_new_article(new_articles: list):
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    for article in new_articles:
        sent = (
            await UseMySQL.run_sql(
                "SELECT url FROM sent_urls WHERE service = %s AND url = %s",
                (SERVICE_NAME, article),
            )
            != []
        )
        if sent:
            continue
        await channel.send(article)
        while True:
            title = await Crawler.get_article_title(article)
            if title != "ERROR":
                break
        await UseMySQL.run_sql(
            "INSERT INTO sent_urls (url, title, category, service) VALUES (%s,  %s, %s, %s)",
            (article, title, "new_article", SERVICE_NAME),
        )


async def main():
    while True:
        try:
            new_articles = await Crawler.get_new_articles()
            if new_articles != "ERROR":
                await send_new_article(new_articles)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
        await asyncio.sleep(60)


@client.command()
async def test(ctx: commands.Context):
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        await ctx.send("F.R.I.D.A.Y. is working!")


@client.event
async def on_ready():
    global task
    await UseMySQL.init_pool()
    await Crawler.init_session()
    print("F.R.I.D.A.Y. is ready!")
    if task is None or task.done():
        task = asyncio.create_task(main())


client.run(TOKEN)
