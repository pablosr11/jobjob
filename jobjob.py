from itertools import cycle
from lxml.html import fromstring, HtmlElement
from urllib import request, error, parse
from http.client import HTTPResponse
from random import random
from time import sleep
import feedparser
from typing import Union, List, Dict
from dataclasses import dataclass
import concurrent.futures
from datetime import datetime


GET_TIMEOUT = 5  # how long do we wait per request?
URL_HEADERS = "https://udger.com/resources/ua-list/browser-detail?browser=Chrome"
URL_PROXY = "https://www.sslproxies.org/"
PROXY_CATEGORY = "elite"  # what proxies do we want?
USER_AGENTS_MAX = 50  # how many user agents do we store?
CRAWLING_BATCH = 3
NUMBER_OF_WORKERS = CRAWLING_BATCH
SLEEP_BETWEEN_BATCHES = 10


class BaseSpider:
    @staticmethod
    def remove_parameters_url(url: str):
        return url.split("?")[0]

    @staticmethod
    def chunks(lst: list, chunk: int):
        for i in range(0, len(lst), chunk):
            yield lst[i : i + chunk]

    @classmethod
    def crawling_batches(cls, links: List[str]):
        return cls.chunks(links, CRAWLING_BATCH)


class SOSpider(BaseSpider):
    def __init__(self, data: Union[feedparser.FeedParserDict, HTTPResponse]):
        self.content = data
        self.jobs = []

    def extract_urls_feed(self):
        self.to_crawl = [
            self.remove_parameters_url(entry["link"])
            for entry in self.content["entries"]
        ]

    @classmethod
    def build_job(cls, data):
        return Job(
            title=cls.get_title(data),
            id=1,
            link="",
            company="Bento",
            location="London",
            raw_data=data,
        )

    @staticmethod
    def get_title(data: str):
        return data.xpath("//h1[contains(@class, 'headline')]/a/text()")[0]


class Downloader:
    def __init__(self, timeout=GET_TIMEOUT):
        self.headers_pool = self.get_headers_pool()
        self.proxy_pool = self.get_proxy_pool()
        self.timeout = timeout
        self.setup_downloader()
        print(
            f"- Downloader initialized\n- IP: {self.proxy['http']}\n- UA: {self.header['User-Agent']}"
        )

    def __repr__(self):
        return repr(f"<Downloader with {self.timeout}s timeout>")

    @classmethod
    def get_proxy_pool(cls):
        response = cls.get_request_fixed_headers(URL_PROXY)
        response_content = response.read()
        proxies = cls.parse_proxy_site(response_content)
        return cycle(proxies)

    @classmethod
    def parse_proxy_site(cls, html: str) -> set:
        return {
            cls.concatenate_host_and_port(element)
            for element in cls.get_valid_proxies(html)
        }

    @staticmethod
    def concatenate_host_and_port(element: HtmlElement) -> str:
        return ":".join(
            [element.xpath(".//td[1]/text()")[0], element.xpath(".//td[2]/text()")[0]]
        )

    @staticmethod
    def get_valid_proxies(html: str, category: str = PROXY_CATEGORY) -> set:
        parser = fromstring(html)
        return {
            element
            for element in parser.xpath("//tbody/tr")
            if element.xpath(f".//td[5][contains(text(),{category})]")
        }

    @classmethod
    def get_headers_pool(cls):
        response = cls.get_request_fixed_headers(URL_HEADERS)
        response_content = response.read()
        user_agents = cls.parse_headers_site(response_content)
        return cycle(user_agents)

    @staticmethod
    def parse_headers_site(html: str, max_ua=USER_AGENTS_MAX) -> list:
        parser = fromstring(html)
        return [ua for ua in parser.xpath("//tr/td/p/a/text()")][:max_ua]

    def get_headers(self):
        user_agent = next(self.headers_pool)
        self.header = {"User-Agent": user_agent}

    def get_proxy(self):
        proxy = next(self.proxy_pool)
        self.proxy = {"http": proxy, "https": proxy}
        self.setup_urllib_proxy()

    def setup_urllib_proxy(self):
        proxy_support = request.ProxyHandler(self.proxy)
        opener = request.build_opener(proxy_support)
        request.install_opener(opener)

    def setup_downloader(self):
        self.get_headers()
        self.get_proxy()

    def get_site_response(self, url: str) -> HTTPResponse:
        while True:
            try:
                response = self.get_request(url)
                print(f"Success - {self.proxy['http']} - {url}")
                break
            except error.URLError as e:
                print(f"Failed - {self.proxy['http']} - {url} - {e}")
                self.setup_downloader()
        return response

    def get_site_content(self, url: str) -> str:
        while True:
            try:
                response = self.get_request(url)
                print(f"Success - {self.proxy['http']} - {url}")
                break
            except error.URLError as e:
                print(f"Failed - {self.proxy['http']} - {url} - {e}")
                self.setup_downloader()
        return response.read()

    def get_request(self, url: str) -> HTTPResponse:
        r = request.Request(url, headers=self.header)
        return request.urlopen(r, timeout=GET_TIMEOUT)

    @staticmethod
    def get_request_fixed_headers(url: str) -> HTTPResponse:
        r = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return request.urlopen(r, timeout=GET_TIMEOUT)

    def concurrent_request(self, urls: list, spider: SOSpider):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_url = {
                executor.submit(self.get_site_content, url): url for url in urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = fromstring(future.result())
                except Exception as exc:
                    print(f"{url} generated an exception: {exc}")
                else:
                    spider.jobs.append(Job.MAPPING[parse.urlparse(url).netloc](data))
                    print(f"Loaded {url}")


@dataclass
class Job:
    id: int
    title: str
    link: str
    company: str
    location: str
    min_salary: int = 0
    max_salary: int = 0
    date_posted: datetime = None
    details: List[Dict[str, str]] = None
    technologies: List[str] = None
    text: str = ""
    benefits: str = ""
    raw_data: str = ""

    MAPPING = {"stackoverflow.com": SOSpider.build_job}


if __name__ == "__main__":

    d = Downloader()

    query = "python"
    city = "london"
    salary = "60000"
    base_url = f"https://stackoverflow.com/jobs/feed"
    url_q = f"{base_url}?q={query}"
    url_s = f"{base_url}?s={salary}"
    url_c = f"{base_url}?l={city}"
    url = f"{base_url}?q={query}&l={city}&s={salary}"

    ### get main site (no proxy used here)
    response = feedparser.parse(r"/Users/ps/repos/jobjob/pythonlondon60k.txt")
    # response = feedparser.parse(url)

    ## create instance of spider for that site with the contents
    spider = SOSpider(response)

    ## get all links to jobs - store them in downloader? in spider?
    spider.extract_urls_feed()

    ## scrape all of them in batches(5-15), after every batch, wait X s and change proxy/header
    for batch in list(spider.crawling_batches(spider.to_crawl))[:1]:
        print(f"\n\n-- Starting {batch}\n")
        d.concurrent_request(batch, spider)
        print("\n-- batch ended\n\n")
        sleep(random() * SLEEP_BETWEEN_BATCHES)

    import pdb

    pdb.set_trace()

    # proxies in the uk? europe? multiprocessing + proxies lookup
    # what do we do with the concurrent requests?

