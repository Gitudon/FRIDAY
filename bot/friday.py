import asyncio
import os
import time
import requests
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import mysql.connector

TOKEN = os.getenv("TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID"))
intent = discord.Intents.default()
intent.message_content = True
client = commands.Bot(command_prefix="-", intents=intent)
target_url = "https://marvel.disney.co.jp/news"


# MySQLの接続設定
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


async def run_sql(sql: str, params: tuple):
    conn = get_connection()
    cursor = conn.cursor(buffered=True)
    if params != ():
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    if sql.strip().upper().startswith("SELECT"):
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    else:
        conn.commit()
        cursor.close()
        conn.close()
        return


async def get_new_articles():
    try:
        time.sleep(1)
        response = requests.get(target_url)
        soup = BeautifulSoup(response.text, "html.parser")
        targets = soup.find_all("div", class_="text-content")
        new_articles = []
        for target in targets:
            new_articles.append(target.find("a").get("href"))
        return new_articles
    except Exception as e:
        print(e)
        return "ERROR"


async def get_article_title(url):
    try:
        time.sleep(1)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").text.strip()
        return title
    except Exception as e:
        print(e)
        return "ERROR"


async def send_new_article(new_articles):
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    sent_urls = await run_sql(
        "SELECT url FROM sent_urls WHERE service = 'FRIDAY'",
        (),
    )
    for i in range(len(sent_urls)):
        if type(sent_urls[i]) is tuple:
            sent_urls[i] = sent_urls[i][0]
    for article in new_articles:
        if article not in sent_urls:
            await channel.send(article)
            while True:
                title = await get_article_title(article)
                if title != "ERROR":
                    break
            await run_sql(
                "INSERT INTO sent_urls (url, title, category, service) VALUES (%s,  %s, %s, %s)",
                (article, title, "new_article", "FRIDAY"),
            )


@client.command()
async def test(ctx):
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        await ctx.send("F.R.I.D.A.Y. is working!")


@client.event
async def on_ready():
    print("F.R.I.D.A.Y. is ready!")
    while True:
        new_articles = await get_new_articles()
        if new_articles != "ERROR":
            await send_new_article(new_articles)
            await asyncio.sleep(60)


client.run(TOKEN)
