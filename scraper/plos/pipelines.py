from pdb import set_trace as bp
import os

import pandas as pd
from pathlib import Path
import requests

from logger import get_logger
log = get_logger(__name__)


class SaveResource:
    dataset = None
    destination_file = ""
    batch_df = []

    def open_spider(self, spider) -> None:
        self.batch_df = []
        self.destination_path = spider.settings.get("DESTINATION_PATH")


        self.documents_path = Path(f"{self.destination_path}/PDFS")
        self.pages_path = Path(f"{self.destination_path}/PAGES")

        self.destination_file = os.path.join(self.destination_path,
                                             spider.settings.get("PERSISTENCE_FILENAME"))

        if not self.pages_path.exists():
            self.pages_path.mkdir(parents=True)

        if not self.documents_path.exists():
            self.documents_path.mkdir(parents=True)

        if Path(self.destination_file).is_file():
            self.dataset = pd.read_csv(self.destination_file)
        else:
            self.dataset = pd.DataFrame(columns=["doi",
                                                 "title",
                                                 "content_filepath",
                                                 "meta_filepath",
                                                 "resource_filepath",
                                                 "resource_url"])

    def process_item(self, item, spider):
        # saving here
        try:
            resource_url = item["resource_url"]
            doi = item["doi"]
            doc_filename = Path(os.path.join(
                self.documents_path, f"{doi}.pdf"))
            meta_filename = Path(os.path.join(
                self.pages_path, f"{doi}-meta.html"))
            page_filename = Path(os.path.join(
                self.pages_path, f"{doi}-page.html"))

            if not meta_filename.parent.exists():
                meta_filename.parent.mkdir(parents=True)

            if not doc_filename.parent.exists():
                doc_filename.parent.mkdir(parents=True)

            r = requests.get(resource_url, stream=True)

            if r.status_code != 200:
                raise((f"An error ocurred trying to gather the PDF file of the"
                       f"item {doi}: status_code {r.status_code}"))

            # Persisting resources
            doc_filename.write_bytes(r.content)

            for ix, text in enumerate(item["article-meta"]):
                meta_filename = Path(os.path.join(
                    self.pages_path, f"{doi}-meta_{ix}.html"))
                meta_filename.write_text(text)

            for ix, text in enumerate(item["article-content"]):
                page_filename = Path(os.path.join(
                    self.pages_path, f"{doi}-page_{ix}.html"))
                page_filename.write_text(text)

            item["resource_filepath"] = str(doc_filename)

            self.batch_df.append(item)

            return item
        except Exception as ex:
            log.error(ex)

    def close_spider(self, spider):
        log.info(f"Persisting reference dataset {self.destination_file}")
        self.dataset = pd.concat([self.dataset, pd.DataFrame(self.batch_df)])
        self.dataset.to_csv(self.destination_file, index=False)
