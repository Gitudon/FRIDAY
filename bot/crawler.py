from common import *
from use_mysql import UseMySQL


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
