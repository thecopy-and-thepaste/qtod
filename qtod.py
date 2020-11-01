"""
This script contains the complete pipeline to gather and acquire the resources from
the site PLOS.

1. Search vía PLOS API all the dois that match our quuery, defined by queries
2. We scrap the page doi.org which redirect us to the resource. Here we get the document in
    pdf and html/xml format.
"""
import logging
from pdb import set_trace as bp
import argparse
import json
import time

from pathlib import Path
from uuid import uuid4
from typing import List
from multiprocessing import Process, Queue

from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer

from gatherer.plos import PlosGatherer

from scraper.plos.spiders import PlosSpider
from scraper.plos import settings as plos_settings

from pathlib import Path

from logger import get_logger, debugger

log = get_logger(__name__)
debug = debugger.debug

QUERY_DEFAULTS = {
    "query": lambda: {},
    "reference_file": lambda: None,
    "spider_settings": lambda: {},
    "id": lambda: str(uuid4()),
    "page_span": lambda: 100
}
start_process = False
# region mappers for endpoint


def override_spider_settings(settings: Settings, new_settings: dict) -> Settings:
    overriden_settings = []
    for k, v in new_settings.items():
        if k in settings.attributes.keys():
            settings[k] = v
            overriden_settings.append(f"{k}-{v}")

    if len(overriden_settings) > 0:
        overriden_settings = "\n".join(overriden_settings)
        log.info((f"The following settings were overriden:\n"
                  f"{overriden_settings}"))

    return settings


def plos_crawler(endpoint: str, query_settings: List[dict], queue):
    assert len(query_settings) > 0,\
        "No queries configured. See the query structure in TODO:"

    # We have n-queries
    for qs in query_settings:
        try:
            if len(qs.items()) == 0:
                log.warn("No queries configured. See the query structure in TODO:")
                continue

            # opts of the settings of the current query
            query = qs["query"]
            spider_settings = qs["spider_settings"]

            # This executes the queries defined and gets a generator to crawl
            # It returns List[query_key, dois]
            dois = PlosGatherer(query).gather(shuffle=True)

            # Building CrawlerRunner with the options defined in
            # the settings file
            crawler_settings = Settings()
            crawler_settings.setmodule(plos_settings)

            crawler_settings = override_spider_settings(crawler_settings,
                                                        spider_settings)
            runner = CrawlerRunner(settings=crawler_settings)

            # This process longs time query["length"] / page_span * burn_out_time
            # PLOS endpoint blocks if you make several requests in a short span of time
            for doi in dois:
                urls = list(
                    map(lambda x: f"https://doi.org/{x}", doi))
                queue.put((endpoint, urls, runner))

            # query_filepath = Path((f'{q["spider_settings"]["DESTINATION_PATH"]}/'
            #                        f'query_{"_".join(q["query"].keys())}.json'))

        except Exception as ex:
            log.error(ex)
            raise
# endregion


def extend(default_file: dict, config_file: dict) -> dict:
    assert len(config_file.items()) > 0, \
        "Yuo have to set the desired query for a particular endpoint"

    query_endpoint = {}

    for endpoint, configs in config_file.items():
        query_endpoint[endpoint] = []
        temp = {}
        if not endpoint in MAPPER_CRAWLER:
            log.warning((f"The endpoint: {endpoint} is not valid. \n"
                         f"Check the endpoint defined in the following section"))
            continue

        for conf in configs:
            # Options for each query_endpoint are
            # query: dict
            # reference_file: str
            # spider_settings: dict
            for _, val in conf.items():
                temp = {}
                for _def in QUERY_DEFAULTS.keys():
                    temp[_def] = conf.get(_def, QUERY_DEFAULTS[_def]())

            query_endpoint[endpoint].append(temp)

    return query_endpoint


MAPPER_CRAWLER = {"PLOS": plos_crawler}
MAPPER_SPIDER = {"PLOS": PlosSpider}

if __name__ == "__main__":
    default_config = ""
    # loading default config
    try:
        with open("defaults.json", mode="r") as def_file:
            default_config = json.load(def_file)
    except Exception as ex:
        # Fired if you delete or misform the defaults.json file
        log.error(ex)
        raise

    # Since there are lots of json config files, the only option
    # to config the queries is vía settings-file
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--config_file",
                        help="Config file for the queries. See TODO:")
    parser.add_argument("-d", "--debug",  action='store_true',
                        help="Enables debug mode to trace the progress of your searching")
    ARGS = parser.parse_args()

    get_logger("DEBUG").setLevel(logging.DEBUG)
    queries_opts = None

    if ARGS.config_file:
        temp = Path(ARGS.config_file)
        if temp.exists():
            with open(temp) as _f:
                queries_opts = json.load(_f)

    # we have n-queries for endpoint
    # Each query has
    # query
    # page_span
    # file of reference
    # setting for the spider
    runners_queue = Queue()
    queries_endpoint = extend(default_config, queries_opts)

    # This process is way faster than the actual crawling of the documents
    for k, query_config in queries_endpoint.items():
        # We have n-queries for each endpoint
        # MAPPER_CRAWLER.get(k, None)(k, query_config, runners_queue)
        p = Process(target=MAPPER_CRAWLER.get(k, lambda w, x, y: log.warning(f"Endpoint not supported")),
                    args=(k, query_config, runners_queue))

        p.daemon = True
        p.start()

    time.sleep(10)

    @defer.inlineCallbacks
    def crawl():
        while not runners_queue.empty():
            endpoint, urls, runner = runners_queue.get()
            debug(f"CRAWLING at {endpoint}")
            # For each batch we scrap the pdf and the article in html
            # So, we run the crawler for the dois resulting
            yield runner.crawl(MAPPER_SPIDER.get(endpoint), start_urls=urls)

        reactor.stop()

    crawl()
    reactor.run()
