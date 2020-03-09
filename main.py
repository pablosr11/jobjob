import requests
from lxml.html import fromstring, HtmlElement
from lxml import etree
from ast import literal_eval
from urllib.parse import urlparse
from typing import Dict
from stem import Signal, SocketError
from stem.control import Controller
from random import choice
import unicodedata


class Downloader:
    def __init__(self, timeout=10, reset=20):
        self.timeout = timeout
        self.counter = reset
        self.get_proxies_tor()
        self.get_new_user_agents()
        self.get_headers()

    def get_proxies_tor(self) -> Dict[str, str]:
        self.get_new_proxy_tor()
        proxies = {
            "http": "socks5://127.0.0.1:9050",
            "https": "socks5://127.0.0.1:9050",
        }
        self.proxy = proxies

    @staticmethod
    def get_new_proxy_tor() -> None:
        try:
            with Controller.from_port(port=9051) as c:
                c.authenticate()
                c.signal(Signal.NEWNYM)
        except SocketError as e:
            raise Exception(f"Tor service not running - {e}")

    def get_headers(self) -> Dict:
        user_agent = choice(self.user_agents)
        headers = {"User-Agent": user_agent}
        self.headers = headers

    def get_new_user_agents(self):
        url = "https://udger.com/resources/ua-list/browser-detail?browser=Chrome"
        tree = self.get_html(url)
        user_agents = [ua for ua in tree.xpath("//tr/td/p/a/text()")]
        self.user_agents = user_agents

    def check_reset_proxy(self):
        if self.counter == 0:
            self.get_new_proxy_tor()
            print(f"Resetting proxy")
            self.counter = 20
        self.counter -= 1

    def get_html(self, url: str, header=None) -> HtmlElement:
        self.check_reset_proxy()
        with requests.get(
            url, self.proxy, headers=header, timeout=self.timeout
        ) as page:
            print(f"Getting - {url} - {page.status_code} - using {header}")
            tree = fromstring(page.content)
        return tree

    def get_and_rotate(self, url: str):
        self.get_headers()
        while True:
            try:
                tree = self.get_html(url, self.headers)
                break
            except requests.exceptions.RequestException as e:
                print(f"Failed - {url} - {e}")
                self.get_headers()
                self.get_proxies_tor()
        return tree


class Spider:
    def __init__(self, url):
        self.url = urlparse(url)
        self.dd = Downloader()
        self.content = self.dd.get_and_rotate(url=url)

    def parse(self):
        MAPPING[self.url.netloc](self)

    def stackoverflow(self):
        # #just parse, and send from here to X using self.url
        jobs = []
        for job in self.content.xpath("//item"):
            job_post = self.so_get_job(job)
            jobs.append(job_post)
        return jobs

    def so_get_job(self, job_content) -> Dict[str, str]:
        job_post = self.so_get_basic_info(job_content, {})
        detail_tree = self.dd.get_and_rotate(url=job_post["link"])
        detail_data = literal_eval(
            detail_tree.xpath("/html/head/script[@type='application/ld+json']/text()")[
                0
            ].strip()
        )
        job_post = self.so_get_detail_info(detail_data, job_post)
        return job_post

    @staticmethod
    def get_base_url(url) -> str:
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def so_get_basic_info(
        self, job_xml: HtmlElement, datapod: Dict[str, str] = None
    ) -> Dict[str, str]:
        datapod["jid"] = job_xml.xpath("guid/text()")
        datapod["link"] = f"{self.get_base_url(url)}/jobs/{datapod['jid'][0]}"
        datapod["title"] = job_xml.xpath("title/text()")
        datapod["location"] = job_xml.xpath("location/text()")
        datapod["technology"] = job_xml.xpath("category/text()")
        if job_xml.xpath("description/text()"):
            datapod["description"] = unicodedata.normalize(
                "NFKD",
                " ".join(
                    etree.XPath("//text()")(
                        fromstring(job_xml.xpath("description/text()")[0])
                    )
                ),
            )
        return datapod

    def so_get_detail_info(
        self, detail: Dict, datapod: Dict[str, str] = None
    ) -> Dict[str, str]:
        datapod["date_posted"] = detail.get("datePosted", None)
        datapod["min_salary"] = (
            detail.get("baseSalary", {}).get("value", {}).get("minValue", None)
        )
        datapod["max_salary"] = (
            detail.get("baseSalary", {}).get("value", {}).get("maxValue", None)
        )
        datapod["company"] = detail.get("hiringOrganization", {}).get("name", None)
        return datapod


MAPPING = {"stackoverflow.com": Spider.stackoverflow}
if __name__ == "__main__":

    # Refactor classes (Job(data container) - Spider(starting url, to scrape) - Downloader
    # speed up

    # MAPPING = {"stackoverflow.com": so_get_data}
    query = "junior"
    city = "london"
    salary = "50000"

    url = f"https://stackoverflow.com/jobs/feed?q={query}&l={city}&d=20&u=Km&s={salary}&c=GBP"
    ss = Spider(url)
    jobs = ss.parse()

    # jobs = MAPPING[urlparse(url).netloc](url)
    # print(
    #     f"Finished: In total, {len(jobs)} jobs found for {query} in {city} for {salary} pounds"
    # )
