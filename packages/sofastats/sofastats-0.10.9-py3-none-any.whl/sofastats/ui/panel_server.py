import os
from pathlib import Path
from subprocess import Popen
from time import sleep
from webbrowser import open_new_tab

def serve():
    cwd = Path(__file__).parent
    try:
        os.chdir(cwd)
    except FileNotFoundError as e:
        print(f"Can't change directory to '{cwd}' for some reason. Orig error: {e}")
    Popen(f"panel serve ui.py", shell=True)
    sleep(2)  ## to give server time to be ready before tab opens
    open_new_tab("http://localhost:5006/ui")

if __name__ == '__main__':
    serve()
