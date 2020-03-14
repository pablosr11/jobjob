from itertools import cycle
from lxml.html import fromstring, HtmlElement
from urllib import request, error
from http.client import HTTPResponse

# multiprocessing
# https://realpython.com/async-io-python/
# https://docs.python.org/3/library/concurrent.futures.html

TIMES_TO_RESET_SETUP = 10  # how many craws until changing proxy/header?
GET_TIMEOUT = 15  # how long do we wait per request?
URL_HEADERS = "https://udger.com/resources/ua-list/browser-detail?browser=Chrome"
URL_PROXY = "https://www.sslproxies.org/"
PROXY_CATEGORY = "elite"  # what proxies do we want?
USER_AGENTS_MAX = 50  # how many user agents do we store?

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
        proxies = cls.parse_proxy_site(response.read())
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
        user_agents = cls.parse_headers_site(response.read())
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

    def check_reset(self):
        self.reset_counter -= 1
        if self.reset_counter <= 0:
            self.setup_downloader()
            self.reset_counter = TIMES_TO_RESET_SETUP
            print(
                f"Resetting downloader. Last used: {self.proxy['http']} - {self.header['User-Agent']}"
            )

    def get_site(self, url: str):
        self.check_reset()
        while True:
            try:
                response = self.get_request(url)
                print(f"Success - {response.status} - {url} - {self.proxy['http']}")
                break
            except error.URLError as e:
                print(
                    f"Failed - {url} - {self.proxy['http']} - {self.header['User-Agent']}\n{e}"
                )
                self.setup_downloader()
        return response

    def get_request(self, url: str):
        return request.urlopen(
            request.Request(url, headers=self.header), timeout=GET_TIMEOUT
        )

    @staticmethod
    def get_request_fixed_headers(url: str) -> HTTPResponse:
        return request.urlopen(
            request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=GET_TIMEOUT,
        )


if __name__ == "__main__":
    d = Downloader()
    from time import sleep

    query = "junior"
    city = "london"
    salary = "50000"
    url = f"https://stackoverflow.com/jobs/feed?q={query}&l={city}&d=20&u=Km&s={salary}&c=GBP"

    while True:
        d.get_site(url)
        sleep(5)
