from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http.client import HTTPResponse
from itertools import cycle
from json import loads
from random import random
from time import sleep
from typing import Any, Dict, List
from unicodedata import normalize
from urllib import error, parse, request

import feedparser
from lxml.html import HtmlElement, fromstring, tostring

from jobjob.database_app import crud, models
from jobjob.database_app.database import SessionLocal

GET_TIMEOUT = 10  # how long do we wait per request? the read timeout comes from here
URL_HEADERS = "https://udger.com/resources/ua-list/browser-detail?browser=Chrome"
URL_PROXY = "https://www.sslproxies.org/"
PROXY_CATEGORY = "elite"  # what proxies do we want?
USER_AGENTS_MAX = 50  # how many user agents do we store?
CRAWLING_BATCH = 3  # how many jobs do we parse concurrently
NUMBER_OF_BATCHES = 1  # how many batches of job do we go for?
NUMBER_OF_WORKERS = CRAWLING_BATCH
SLEEP_BETWEEN_BATCHES = 0

QUERY = "python"
CITY = "london"
BASE_URL = f"https://stackoverflow.com/jobs/feed"


class BaseSpider(ABC):
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

    @abstractmethod
    def add_job(self, data):
        ...


class SOSpider(BaseSpider):
    def __init__(
        self, data: Any,
    ):
        # We should get firjst all links, then filter out links existing in DB, then start scraping
        # By using feedparser, we already have most of the data we need in the data we use to create the spider. a more
        #   tradigional spider would get started by a URL and then either extract info on that one ot find links and iterate

        # main site to scrape links from
        self.content = data

        self.downloader = Downloader()

        # self.start_url = start_url
        self.db = SessionLocal()

        self.extract_urls_feed()

        ## add an attribute to keep track of work done

    # is it too slow to check for links before scraping?
    # because of the filtering, new queries wont include jobs that already
    # got caught by other queries
    def extract_urls_feed(self):
        """Add to_crawl links to the spider if we dont have them in the db already"""
        self.to_crawl = [
            self.remove_parameters_url(entry["link"])
            for entry in self.content["entries"]
            if not crud.get_job_by_link(
                self.db, parse.urlparse(self.remove_parameters_url(entry["link"])).path
            )
        ]

    def persist_details(self, details: Dict, job_id: int):
        return crud.create_job_detail(
            self.db,
            models.Detail(
                job_type=details.get("Job type", ""),
                role=details.get("Role", ""),
                experience_level=details.get("Experience level", ""),
                industry=details.get("Industry", ""),
                company_size=details.get("Company size", ""),
                company_type=details.get("Company type", ""),
                job_id=job_id,
            ),
        )

    def persist_skills(self, skills: List, job_id: int):
        return [
            crud.create_job_skill(self.db, models.Skill(title=skill, job_id=job_id))
            for skill in skills
        ]

    def persist_rawdata(self, raw_data: str, job_id: int):
        return crud.create_job_rawdata(
            self.db, models.JobRawData(job_id=job_id, raw_data=raw_data)
        )

    # should inherit all model instances? or all non-model instances?
    def persist(
        self, job: models.Job, skills: List, details: Dict[str, str], raw_data: str
    ):
        db_job = crud.get_job(self.db, job.job_id)
        if db_job:
            print(f"== Job - {db_job.title} already exists")
            return db_job, db_job.skills

        new_job = crud.create_job(self.db, job)
        new_skills = self.persist_skills(skills, new_job.id)
        new_details = self.persist_details(details, new_job.id)
        new_raw_data = self.persist_rawdata(raw_data, new_job.id)

        print(f"== Added - {new_job.title} with {len(new_skills)} skills")

        return new_job, new_skills, new_details, new_raw_data

    def add_job(self, data: bytes):
        tree = fromstring(data)
        job = self.build_job(tree)
        skills = self.get_skills(tree)
        details = self.get_details(tree)
        raw_data = tostring(tree)
        self.persist(job, skills, details, raw_data)

    @staticmethod
    def clean_up_text(text):
        unwanted_chars = ["\\n", "\t", "\\r", ":", "\xa0"]
        for char in unwanted_chars:
            text = text.replace(char, "").strip()
            text = text.replace("â\x80\x93", "-")
        return text

    @staticmethod
    def list_to_n_tuple(lst: List, size: int = 2):
        return dict(zip(lst[::size], lst[1::size]))

    @classmethod
    def build_job(cls, data: HtmlElement):

        json_data = cls.get_json_data(data)

        return models.Job(
            title=cls.get_title(data),
            job_id=cls.get_id(data),
            link=cls.get_link(data),
            company=cls.get_company(data),
            city=cls.get_city(json_data),
            postal_code=cls.get_postal_code(json_data),
            min_salary=cls.get_min_salary(json_data),
            max_salary=cls.get_max_salary(json_data),
            date_posted=cls.get_date_posted(json_data),
            benefits=cls.get_benefits(data),
            text=cls.get_text(data),
        )

    @classmethod
    def get_json_data(cls, data: str):
        try:
            # normal form NFKD will replace all compatibility characters with their equivalents
            normalized = normalize(
                "NFKD",
                data.xpath("//script[contains(@type,'application/ld+json')]/text()")[
                    0
                ].strip(),
            )
            json_data = loads(normalized)
        except ValueError as exc:
            json_data = {}
            print(f"""Error on {cls.get_link(data)}\n{exc}\n""")

        return json_data

    @staticmethod
    def get_title(data: str):
        return data.xpath("//h1[contains(@class, 'headline')]/a/text()")[0]

    @staticmethod
    def get_id(data: str):
        return data.xpath("//head/link[@rel='canonical']/@href")[0].split("/")[-2]

    @staticmethod
    def get_link(data: str):
        return parse.urlparse(data.xpath("//head/link[@rel='canonical']/@href")[0]).path

    @staticmethod
    def get_company(data: str):
        return data.xpath(
            "//a[contains(@class,'fc-black-700') or contains(@class, 'employer')]/text()"
        )[0]

    @staticmethod
    def get_city(json_data: str):
        return (
            json_data.get("jobLocation", {})[0]
            .get("address", {})
            .get("addressLocality", None)
        )

    @staticmethod
    def get_postal_code(json_data: str):
        return (
            json_data.get("jobLocation", {})[0]
            .get("address", {})
            .get("postalCode", None)
        )

    @staticmethod
    def get_min_salary(json_data: Dict):
        return json_data.get("baseSalary", {}).get("value", {}).get("minValue", None)

    @staticmethod
    def get_max_salary(json_data: Dict):
        return json_data.get("baseSalary", {}).get("value", {}).get("maxValue", None)

    @staticmethod
    def get_date_posted(json_data: str):
        date = json_data.get("datePosted", None)
        return datetime.strptime(date, "%Y-%m-%d")

    @staticmethod
    def get_details(data: str):
        all_details = [
            SOSpider.clean_up_text(x)
            for x in data.xpath(
                "//section/div[contains(@class,'job-details')]/div/div//text()"
            )
            if SOSpider.clean_up_text(x)
        ]
        return SOSpider.list_to_n_tuple(all_details)

    @staticmethod
    def get_skills(data: str):
        return data.xpath("//section[@class]/div/a/text()")

    @staticmethod
    def get_benefits(data: str):
        return ". ".join(
            [
                x.strip()
                for x in data.xpath(
                    "//section[contains(@class, 'benefits')]/ul/li/@title"
                )
                if x.strip()
            ]
        )

    @staticmethod
    def get_text(data: str):
        return " ".join(
            [
                x.strip()
                for x in data.xpath("//section[contains(@class, 'body')]//text()")
                if x.strip()
            ]
        )


class Downloader:
    def __init__(self, timeout=GET_TIMEOUT):
        # Collect list of headers/proxies
        self.headers_pool = self.get_headers_pool()
        self.proxy_pool = self.get_proxy_pool()

        self.timeout = timeout
        self.setup_downloader()
        print(
            f"- Downloader init\n- IP: {self.proxy['http']}\n- UA: {self.header['User-Agent']}"
        )

    @classmethod
    def get_headers_pool(cls):
        response = cls.get_request_fixed_headers(URL_HEADERS)
        user_agents = cls.parse_headers_site(response.read())
        return cycle(user_agents)

    @staticmethod
    def get_request_fixed_headers(url: str) -> HTTPResponse:
        r = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return request.urlopen(r, timeout=GET_TIMEOUT)

    @staticmethod
    def parse_headers_site(html: str, max_ua=USER_AGENTS_MAX) -> list:
        parser = fromstring(html)
        return [ua for ua in parser.xpath("//tr/td/p/a/text()")][:max_ua]

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

    def concurrent_request(self, urls: list, spider: SOSpider):
        with ThreadPoolExecutor() as executor:
            future_to_url = {
                executor.submit(self.get_site_content, url): url for url in urls
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(
                        f"\n==========Not Loaded - {url} generated an exception: {exc}\n"
                    )
                else:
                    spider.add_job(data)


MAPPING_SPIDER = {"stackoverflow.com": SOSpider}


def build_url(
    base: str,
    query: str,
    location: str = None,
    salary: int = None,
    remote: bool = False,
):

    start_url = base

    if query:
        start_url += f"?q={sanitise_spaces(query)}"

    if location:
        start_url += f"&l={sanitise_spaces(location)}&d=20&u=Miles"

    if salary:
        start_url += f"&s={salary}&c=GBP"

    if remote:
        start_url += f"&r=true"

    return start_url


def sanitise_spaces(query: str):
    return "+".join(query.split(" "))


def get_host(url: str):
    return parse.urlparse(url).netloc


def trigger_spider(query: str):

    query = sanitise_spaces(query)
    start_url = build_url(base=BASE_URL, query=query)
    host = get_host(start_url)

    print(f"=====SPIDER - Start URL {start_url}")

    try:
        feed_tree = feedparser.parse(start_url)
        # feed_tree = feedparser.parse(r"pythonlondon60k.txt")
    except RuntimeError as exc:
        print("Error while parsing the url - Try standard request")
        raise exc

    spider = MAPPING_SPIDER[host](feed_tree)

    crawl(spider)

    print(f"\n\nFinished --------\n")


def crawl(spider: BaseSpider):

    batches = list(spider.crawling_batches(spider.to_crawl))

    for batch in batches[:NUMBER_OF_BATCHES]:
        print(f"\n-- Starting {batch}\n")
        spider.downloader.concurrent_request(batch, spider)
        sleep(random() * SLEEP_BETWEEN_BATCHES)


# if __name__ == "__main__":
#     trigger_spider("machine learning")
