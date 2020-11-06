# qtod

## Overview

**qtod** (query-to-documents) is intended to gather documents from Open Access literature sites using only customizable queries in regards to topics of interest.

The full process consists of 2 steps:

1. Gather the results of the query using the fields of search. The values are defined in the API of the provider of the documents.
2. Collect the resources from the site and save them in the local file storage.

Users only need to configure the `queries.json` file with the sections related to the specific step in an enpoint, as shown:

```json
"ENDPOINT":{
    "query":{
        [ opts ]
    },
    "spider_settings": {
        [ opts ]
    }
}
```

## Requirements 

- Python 3.7.7


## Configuration for specific endpoints

All the configuration values for different endpoints rely on 2 files, `defaults.json` , and `scraper/ENDPOINT/settings.py`, to be overridden in the `queries.json` file's sections `query` and `spider_settings`, respectively.

In this section, we describe the configuration of the endpoints available to collect documents.

### PLOS

----
PLOS is a nonprofit, Open Access publisher empowering researchers to accelerate progress in science and medicine by leading a transformation in research communication.
____
From <a href="https://plos.org/">PLOS</a>

All the fields available to search vía api are defined in <a href="http://api.plos.org/solr/search-fields/">the documentation section</a>  of the PLOS API.

The `query` section, intended to gather results from the search API, contains 4 values:

- `fields (dict) default: None` : The fields to be queried with the values to search.
- `join_op (string) default: "OR"`: The operator to use to join the fields (possible values `AND`, `OR`).
- `total (int) default: 10`: The max number of results to obtain.
- `page_span (int) default:100`: The number of entries per page.
- `burnout_time (int): default: 10`: Span of time to wait between queries (Since you're querying lots of times to the API, you could be banned, **be polite with this value**)

The `spider_settings` section overrides the values defined in the `scraper/plos/settings.py` file, to be described:

- `DESTINATION_PATH (string)`: Filepath where **HTML** and **PDF** files will be stored.
- `PERSISTENCE_FILENAME (string)`: Filepath where the **CSV** file, with the relation of id, files. and pages is stored. The destination file contains the following fields:
[]
- `DELAY_TIME (int)`: Span of time to acquire each file (Since you're querying lots of times to the API, you could be banned, **be polite with this value**)

### Example

In the `queries.json` file

```json
// Search in the PLOS endpoint
"PLOS": [  
    {
        "query": {
            "fields": {
                // For the abstract field the following values
                "abstract": [
                    "natural",
                    "ecology"
                    ]
                    },
                // Joined by OR
                "join_op": "OR",
                // Total amount of 100 results in pages of 10
                "total": 100,
                "page_span": 10,
            },
            "spider_settings": {
                // HTML and PDF stored here
                "DESTINATION_PATH": "./documents/nat_ec",
                // Waiting 5 secs between downloads
                "DELAY_TIME": 5
            }
        },
        {
            [. . .]
        }
    ]
```

## Usage 

We recommed the usage of qtod in a virtual environment, with either `venv` or `pipenv` over Python 3+, as shown:

```python
 python3 -m venv ./filepath
```

and then, after activate the virtual environment, install the dependencies with:

```python
pip install -r requirements.txt
```

In the main, run the `qtop.py`.

```python
python qtod.py 
optional arguments:
  -f    'Filepath to the config file for the queries'
  -d    'Enables debug mode to trace the progress of your process'
```