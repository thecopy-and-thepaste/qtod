from pdb import set_trace as bp
import os
from typing import List

import requests
import random
import json
import pydash
import time

import pandas as pd

from pathlib import Path

from logger import get_logger, debugger
log = get_logger(__name__)
debug = debugger.debug


class PlosGatherer():
    VALID_OPTIONS = {
        "fields": {"default": None},
        "join_op": {"default": "OR"},
        "total": {"default": 10},
        "burnout_time": {"default": 10},
        "page_span": {"default": 100}
    }

    def __init__(self,
                 query: dict):
        """
        Args:
            json_queries (dict): [Queries to execute in the API PLOS]
            reference_file (str): [We need to add a file with previous results to check duplicated dois]
            burnout_time (int, optional): [Time of waiting between calls, BE POLITE with this value]. Defaults to 20.
            num_entries_per_request (int, optional): [Number of result per request]. Defaults to 50.
        """
        query = self.__parse_query(query)
        debug(query)
        self.str_query = query["str_query"]
        self.burnout_time = query["burnout_time"]
        self.page_span = query["page_span"]
        self.total = query["total"]

    def __parse_query(self, query: dict) -> dict:
        """Creates the string_query property for earch query that is manageable
        by requests.

        The queries should have at least defiend the field to search

        Args:
            queries (dict): [queries to convert]

        Returns:
            List[str]: [string requests]
        """
        for opt, _def in self.VALID_OPTIONS.items():
            if opt not in query and not _def["default"]:
                msg = f"The field {opt} has to de defined"
                log.error(msg)
                raise Exception(msg)
            else:
                query[opt] = query.get(opt, _def["default"])

        fls = query["fields"]
        query["str_query"] = f' {query["join_op"]} '.join(pydash.chain(fls.keys())
                                                          .map(lambda key: [f'{key}:"{val}"' for val in fls[key]])
                                                          .reduce(lambda x, y: x+y, [])
                                                          .value())
        return query

    def gather(self,
               shuffle: bool = True) -> List[str]:
        """
        Calculates the total amount of items found with the query
        Calculate the batches according to num_entries_per_request
        Yields the batch

        Args:
            search_query (str): [query to search in API PLOS]


        Yields:
            Iterator[List[str]]: [List of dois found]
        """
        start = 0
        num_found = float("-inf")
        init_query = (f"http://api.plos.org/search?q={self.str_query}"
                      f'&start={start}&rows=1&fl=id&fq=abstract:*')
        r = requests.get(url=init_query)
        num_found = r.json()["response"]["numFound"]

        debug(f"Found {num_found} entries, got {self.total}")

        batches = range(0, num_found, self.page_span)
        if shuffle:
            batches = list(batches)
            random.shuffle(batches)

        batches = iter(batches)

        dois_gathered = 0
        start = next(batches)

        while start is not None:
            try:
                query = f'q={self.str_query}&start={start}&rows={self.page_span}'
                debug(f"Query: {query}")

                url = f"http://api.plos.org/search?{query}&fl=id&fq=abstract:*"
                r = requests.get(url=url)

                if r.status_code == 200:
                    response = r.json()["response"]
                    docs = response["docs"]
                    batch_dois = list(map(lambda x: x["id"], docs))

                    dois_gathered += len(batch_dois)

                    if self.total:

                        if dois_gathered > self.total:
                            batch_dois = batch_dois[0: -
                                                    (dois_gathered - self.total)]
                            start = None
                            yield batch_dois
                            break

                    yield batch_dois
                    time.sleep(self.burnout_time)
                    start = next(batches)
                else:
                    break
            except Exception as ex:
                print(ex)
