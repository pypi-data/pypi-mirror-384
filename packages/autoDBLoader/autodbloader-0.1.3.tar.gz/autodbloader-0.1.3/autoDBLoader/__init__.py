from .insertLoader import AutoDBLoaderInsertDate
from .extractDB import AutoDBLoaderExtractDate

def insert_date(json_config):
    inserter = AutoDBLoaderInsertDate(json_config)
    return inserter._insertDate(json_config)

def extract_date(json_config):
    extractor = AutoDBLoaderExtractDate(json_config)
    return extractor._extractDate(json_config)

def run_interface():
    """Executa a interface gráfica do AutoDBLoader."""
    from .cli import run  # import atrasado para evitar import circular
    run()
