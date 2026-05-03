from common import *
from crawler import Crawler
from use_mysql import UseMySQL

intent = discord.Intents.default()
intent.message_content = True
client = commands.Bot(command_prefix="-", intents=intent)
task = None


class FRIDAY:
    @staticmethod
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
                await FRIDAY.send_new_article(new_articles)
        except Exception as e:
            await write_log_message(f"{e}", "ERROR")
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
    await write_log_message("Bot is ready!", "INFO")
    if task is None or task.done():
        task = asyncio.create_task(main())


client.run(TOKEN, log_handler=None)
