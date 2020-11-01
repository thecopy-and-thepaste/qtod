BOT_NAME = 'qtop_plos'

ITEM_PIPELINES = {
    'scraper.plos.pipelines.SaveResource': 100
}

DESTINATION_PATH = "./plos_documents"
PERSISTENCE_FILENAME = "dataset.csv"
DELAY_TIME = 5