from unittest import mock

import feedparser
import pytest
from lxml import html
from sqlalchemy import orm

from jobjob.database_app import crud, models
from jobjob.spider_app import spider
from jobjob.spider_app.spider import (BaseSpider, Downloader, SessionLocal,
                                      SOSpider, build_url, get_host,
                                      sanitise_spaces)


@pytest.fixture
def _spider(monkeypatch):
    monkeypatch.setattr(Downloader, "__init__", mock.Mock(return_value=None))
    monkeypatch.setattr(SOSpider, "extract_urls_feed", mock.Mock())
    monkeypatch.setattr(spider, "SessionLocal", mock.Mock())
    sp = SOSpider({"entries":[{"link":"link1"}]})
    sp.to_crawl = ""
    return sp

def one_job():
    return models.Job(job_id=1, link="/whatever/tests")

class TestBaseSpider:
    def test_remove_params_url(self):
        url_with_params = "http://jobjob.com/?q=three"
        expected = "http://jobjob.com/"

        result = BaseSpider.remove_parameters_url(url_with_params)
        assert expected == result

    def test_chunks(self):
        full_list = [1, 2, 3, 4, 5, 6, 3, 2]
        n_chunks = 3
        expected = [[1, 2, 3], [4, 5, 6], [3, 2]]

        result = list(BaseSpider.chunks(full_list, n_chunks))
        assert result == expected

    def test_crawling_batches(self):
        links = ["link1", "link2", "link3"]
        chunk_size = 1
        expected = [["link1"], ["link2"], ["link3"]]

        result = list(BaseSpider.crawling_batches(links, chunk_size))

        assert result == expected

class TestSOSpider:

    def test_init(self, monkeypatch):

        monkeypatch.setattr(Downloader, "__init__", mock.Mock(return_value=None))
        monkeypatch.setattr(SOSpider, "extract_urls_feed", mock.Mock())

        data = "this is a python job"
        spider = SOSpider(data)
        assert spider.content == data
        
    def test_extract_urls_feed(self, monkeypatch):
        # add variation but actually checkin in database
        links = ["link1", "link2", "link3"]
        data = {"entries": [{"link":x} for x in links]}
        monkeypatch.setattr(Downloader, "__init__", mock.Mock(return_value=None))
        monkeypatch.setattr(crud, "get_job_by_link", mock.Mock(return_value=[]))

        spider = SOSpider(data)

        assert spider.to_crawl == links
    
    def test_persist_details(self, monkeypatch, _spider):
        with mock.patch.object(crud, "create_job_detail") as job_detail_mock:
            _spider.persist_details({}, 1)
        job_detail_mock.assert_called()
    
    def test_persist_skills(self, monkeypatch, _spider):
        with mock.patch.object(crud, "create_job_skill") as job_skills_mock:
            _spider.persist_skills(["oneskill"], 1)
        job_skills_mock.assert_called()
    
    def test_persist_rawdata(self, monkeypatch, _spider):
        with mock.patch.object(crud, "create_job_rawdata") as job_rawdata_mock:
            _spider.persist_rawdata("",  1)
        job_rawdata_mock.assert_called()

    def test_persist_all_with_existing_job(self, monkeypatch, _spider):
        monkeypatch.setattr(crud, "get_job", mock.Mock(return_value=one_job()))
        job, _ = _spider.persist(one_job(), 1, 1, 1) # discard skills
        assert job.job_id == one_job().job_id

    def test_persist_all_with_no_existing_job(self, monkeypatch, _spider):
        monkeypatch.setattr(crud, "get_job", mock.Mock(return_value=0))
        monkeypatch.setattr(crud, "create_job", mock.Mock(return_value=one_job()))

        monkeypatch.setattr(SOSpider, "persist_details", mock.Mock(return_value=1))
        monkeypatch.setattr(SOSpider, "persist_skills", mock.Mock(return_value=[]))
        monkeypatch.setattr(SOSpider, "persist_rawdata", mock.Mock(return_value=1))

        job, skills, detail, raw_data = _spider.persist(one_job(), [], {}, "")

        assert job.job_id == detail

    def test_add_job(self, monkeypatch, _spider):
        monkeypatch.setattr(SOSpider, "build_job", mock.Mock())
        monkeypatch.setattr(SOSpider, "get_skills", mock.Mock())
        monkeypatch.setattr(SOSpider, "get_details", mock.Mock())

        with mock.patch.object(SOSpider, "persist") as mock_persist:
            _spider.add_job("<html>")
        
        mock_persist.assert_called()

    @pytest.mark.parametrize("input,expected",[("\\nhola", "hola"), ("hola:hola", "holahola"), ("â\x80\x93hola","-hola")])
    def test_cleanup_text(self, input, expected):
        assert SOSpider.clean_up_text(input) == expected


    def test_list_to_n_tuple(self):
        inp = ["Name", "Sanderson"]
        expected = {"Name":"Sanderson"}
        result = SOSpider.list_to_n_tuple(inp)
        assert result == expected

class TestDownloader:

    def test_init(self,monkeypatch):

        mock_get_headers_pool = mock.Mock(return_value=iter([1,2,3]))
        mock_get_proxy_pool = mock.Mock(return_value=iter([1,2,3]))
        # mock_setup_downloader = mock.Mock()

        monkeypatch.setattr(Downloader, "get_headers_pool", mock_get_headers_pool)
        monkeypatch.setattr(Downloader, "get_proxy_pool", mock_get_proxy_pool)
        # monkeypatch.setattr(Downloader, "setup_downloader", mock_setup_downloader)

        d = Downloader(1)

        for m in [mock_get_headers_pool, mock_get_proxy_pool]:
            m.assert_called()
    
    def test_concurrent_request(self, _spider, monkeypatch):
        assert 0
        
class TestMisc:

    @pytest.mark.parametrize("input,expected", [("software engineer","software+engineer"),(" and the","+and+the"),("oleole","oleole")])
    def test_sanitise_spaces(self, input, expected):
        assert sanitise_spaces(input) == expected

    def test_get_host(self):
        url = "http://marca.com/welcome"
        host = "marca.com"
        assert get_host(url) == host

    def test_build_url(self):
        url = "www.job.com"
        query = "python"
        location = "london"
        salary = 20000
        remote = True
        expected = "www.job.com?q=python&l=london&d=20&u=Miles&s=20000&c=GBP&r=true"
        assert build_url(url, query, location, salary, remote) == expected

    def test_trigger_spider_raise_error(self, monkeypatch):

        mock_sanitise = mock.Mock(return_value="wha343tever")
        mock_build_url = mock.Mock(return_value="asdfasdfa")
        mock_get_host = mock.Mock(return_value="asfasdaf")
        mock_parse = mock.Mock(side_effect=RuntimeError('mocked error'))
        mock_spider_init = mock.Mock(return_value=None)
        mock_crawl = mock.Mock()

        monkeypatch.setattr(spider, "sanitise_spaces", mock_sanitise)
        monkeypatch.setattr(spider, "build_url", mock_build_url)
        monkeypatch.setattr(spider, "get_host", mock_get_host)
        monkeypatch.setattr(feedparser, "parse", mock_parse)

        with pytest.raises(RuntimeError) as e:
            spider.trigger_spider("whatisthis")

        for m in [mock_sanitise, mock_build_url, mock_get_host, mock_parse]:
            m.assert_called()

        for m in [mock_spider_init, mock_crawl]:
            m.assert_not_called()

    def test_trigger_spider(self, monkeypatch):

        mock_sanitise = mock.Mock(return_value="wha343tever")
        mock_build_url = mock.Mock(return_value="asdfasdfa")
        mock_get_host = mock.Mock(return_value="stackoverflow.com")
        mock_parse = mock.Mock(return_value="asdfas")
        mock_spider_init = mock.Mock(return_value=None)
        mock_crawl = mock.Mock()

        monkeypatch.setattr(spider, "sanitise_spaces", mock_sanitise)
        monkeypatch.setattr(spider, "build_url", mock_build_url)
        monkeypatch.setattr(spider, "get_host", mock_get_host)
        monkeypatch.setattr(feedparser, "parse", mock_parse)
        monkeypatch.setattr(SOSpider, "__init__", mock_spider_init)
        monkeypatch.setattr(spider, "crawl", mock_crawl)

        spider.trigger_spider("jaleo")

        for m in [mock_sanitise, mock_build_url, mock_get_host, mock_parse, mock_spider_init, mock_crawl]:
            m.assert_called()

    def test_crawl(self, monkeypatch, _spider):

        mock_crawling_batches = mock.Mock(return_value=[[1,2,3],[2,3,4]])
        mock_concurrent_request = mock.Mock()

        monkeypatch.setattr(BaseSpider, "crawling_batches", mock_crawling_batches)
        monkeypatch.setattr(spider, "SLEEP_BETWEEN_BATCHES", 0)
        monkeypatch.setattr(Downloader, "concurrent_request", mock_concurrent_request)

        spider.crawl(_spider)

        mock_crawling_batches.assert_called()
        mock_concurrent_request.assert_called()
