import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from autoDBLoader import extract_date, insert_date
import py_positron as positron

class API:
    def run(self, params):
        func = params.get("func")
        jsonConfig = params.get("config")
        status = ""
        if func == "insert":
            status = self.insertDate(jsonConfig)
        elif func == "extract":
            status = self.extractDate(jsonConfig)
        else:
            self.ui.document.alert(f"O método ({func}) não existe na biblioteca.")
            
        return status
    
    def insertDate(self, json_config):
        try:
            insert_date(json_config)
            return "Inserção"
        except Exception as e:
            print(f"Erro em insertDate: {e}")
            raise e

    def extractDate(self, json_config):
        try:
            extract_date(json_config)
            return "Extração"
        except Exception as e:
            print(f"Erro em extractDate: {e}")
            raise e


def main(ui):
    api = API()
    api.ui = ui  # vincule a instância para uso posterior
    ui.expose_api = getattr(ui, "window", ui).expose  # ou use ui.window.expose
    try:
        # expõe a função run diretamente via API
        getattr(ui.window if hasattr(ui, "window") else ui, "expose")(api.run)
    except Exception as e:
        print("Erro ao expor run:", e)
    ui.exposed = api  # também defina API exposta

html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "configuracao.html"))
