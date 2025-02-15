import discord
from discord.ext import commands
import asyncio
import os
import requests
from bs4 import BeautifulSoup

TOKEN =  os.getenv("TOKEN")
DISCORD_CHANNEL_ID= int(os.environ.get("DISCORD_CHANNEL_ID"))
intent = discord.Intents.default()
intent.message_content= True
client = commands.Bot(
    command_prefix='-',
    intents=intent
)
target_url="https://marvel.disney.co.jp/news"

async def get_new_articles():
    try:
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

async def send_new_video(buffa_articles,new_articles):
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    flag=False
    for article in new_articles:
        if article not in buffa_articles:
            if flag:
                await channel.send("Sir, I have found some new articles!")
                flag=True
            await channel.send(article)

@client.command()
async def test(ctx):
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        await ctx.send("F.R.I.D.A.Y. is working!")

@client.event
async def on_ready():
    print("F.R.I.D.A.Y. is ready!")
    while True:
        bufffa_articles=await get_new_articles()
        if bufffa_articles!="ERROR":
            break
    while True:
        new_articles = await get_new_articles()
        if new_articles != "ERROR":
            await send_new_video(bufffa_articles,new_articles)
            bufffa_articles=new_articles
            await asyncio.sleep(60)

client.run(TOKEN)