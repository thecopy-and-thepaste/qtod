"""
    This scripts 
"""
import scrapy
import time


from pdb import set_trace as bp

from logger import get_logger, debugger

log = get_logger(__name__)
debug = debugger.debug

class PlosSpider(scrapy.Spider):
    name = "PLOS"
    journal_uri = "https://journals.plos.org"

    def parse(self, response):
        try:
            span_time = self.settings.get("DELAY_TIME")
            doi = "/".join(response.url.split("=")[-1:])
            page = response.url.split("/")[-1]

            debug(f"CRAWLING {page}")

            time.sleep(span_time)
            article_meta = response.xpath('//div[@class = "article-meta"]')\
                .extract()
            article_content = response.xpath('//div[@class = "article-content"]')\
                .extract()

            pdf_resource = response.xpath('//div[@class = "dload-pdf"]/a/@href')\
                .extract()
            title = response.xpath('//h1[@id = "artTitle"]/text()')\
                .extract()

            if len(pdf_resource) != 1:
                log.error((f"We can't find the PDF resource for the item {doi}\n"
                           f"Skipping further process"))
                return
            else:
                pdf_resource = pdf_resource[0]

            if len(title) == 0:
                log.error((f"We can't find the title of the item {doi}\n"
                           f"Please check in meta archive"))

            yield {
                "article-meta": article_meta,
                "article-content": article_content,
                "title": title[0],
                "resource_url": f"{self.journal_uri}{pdf_resource}",
                "doi": doi
            }
        except Exception as ex:
            log.error("An error ocurred while parsing the document")
            log.error(ex)
            raise