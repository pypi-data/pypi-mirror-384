import os
import py_positron as positron
from autoDBLoader.backend.main import main

def run():
    current_dir = os.path.dirname(__file__)
    html_path = os.path.join(current_dir, "frontend", "configuracao.html")
    positron.openUI(
    html_path,
    main,
    title="AutoDBLoader",
    width=1140,
    height=720,
    resizable=True,
    debug=False
)
