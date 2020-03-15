from itertools import cycle
from lxml.html import fromstring, HtmlElement
from urllib import request, error
from http.client import HTTPResponse
from random import random
from time import sleep
import feedparser


TIMES_TO_RESET_SETUP = 10  # how many craws until changing proxy/header?
GET_TIMEOUT = 20  # how long do we wait per request?
URL_HEADERS = "https://udger.com/resources/ua-list/browser-detail?browser=Chrome"
URL_PROXY = "https://www.sslproxies.org/"
PROXY_CATEGORY = "elite"  # what proxies do we want?
USER_AGENTS_MAX = 50  # how many user agents do we store?
SLEEP_BETWEEN_REQUEST = 5
SLEEP_ON_FAILED = 4


class Downloader:
    def __init__(self, timeout=GET_TIMEOUT):
        self.headers_pool = self.get_headers_pool()
        self.proxy_pool = self.get_proxy_pool()
        self.reset_counter = TIMES_TO_RESET_SETUP
        self.timeout = timeout
        self.setup_downloader()
        print(
            f"- Downloader initialized\n- IP: {self.proxy['http']}\n- UA: {self.header['User-Agent']}"
        )

    def __repr__(self):
        return repr(
            f"<Downloader with {self.timeout}s timeout and {self.reset_counter} crawls left>"
        )

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
        self.proxy_handler = proxy_support

    def setup_downloader(self):
        self.get_headers()
        self.get_proxy()

    def check_reset(self):
        self.reset_counter -= 1
        if self.reset_counter <= 0:
            self.setup_downloader()
            self.reset_counter = TIMES_TO_RESET_SETUP
            print(
                f"Resetting downloader. Last used: {self.proxy['http']} - {self.header['User-Agent']}"
            )

    def get_site_response(self, url: str) -> HTTPResponse:
        self.check_reset()
        while True:
            try:
                response = self.get_request(url)
                print(f"Success - {response.status} - {url}")
                break
            except error.URLError as e:
                if hasattr(e, "reason"):
                    print(
                        f"Failed to reach server - {e.reason} - {url} - {self.proxy['http']}"
                    )
                elif hasattr(e, "code"):
                    print(
                        f"Server couldn't fulfill request - {e.code} - {url} - {self.proxy['http']}"
                    )
                sleep(random() * SLEEP_ON_FAILED)
                self.setup_downloader()
        return response

    def get_request(self, url: str) -> HTTPResponse:
        r = request.Request(url, headers=self.header)
        return request.urlopen(r, timeout=GET_TIMEOUT)

    @staticmethod
    def get_request_fixed_headers(url: str) -> HTTPResponse:
        r = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return request.urlopen(r, timeout=GET_TIMEOUT)


class SOSpider:
    def __init__(self, data):
        self.content = data

    def extract_url_feed(self):
        self.to_crawl = [
            self.remove_parameters_url(entry["link"])
            for entry in self.content["entries"]
        ]

    @staticmethod
    def remove_parameters_url(url: str):
        return url.split("?")[0]


if __name__ == "__main__":
    d = Downloader()

    query = "python"
    city = "london"
    salary = "60000"
    url = f"https://stackoverflow.com/jobs/feed?"
    url_q = f"https://stackoverflow.com/jobs/feed?q={query}"
    url_s = f"https://stackoverflow.com/jobs/feed?s={salary}"
    url_c = f"https://stackoverflow.com/jobs/feed?l={city}"
    url_full = (
        f"https://stackoverflow.com/jobs/feed?q={query}&l={city}&s={salary}&c=GBP"
    )

    while True:

        ### get main site (no proxy used here)
        response = feedparser.parse(url)

        ## create instance of spider for that site with the contents
        spider = SOSpider(response)

        ## get all links to jobs - store them in downloader? in spider?
        spider.extract_url_feed()

        ## scrape all of them in batches(5-15), after every batch, wait X s and change proxy/header

        sleep(random() * SLEEP_BETWEEN_REQUEST)
        break
