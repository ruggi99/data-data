import sys
import http.server
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import requests
import logging

logging.basicConfig(level=logging.INFO)

# Install pypxlib, watchdog

data_project_dir = "C:/Data Project/Data Volley 4/Data/"
prod_ip = "192.168.1.121:8000"
dev_ip = "192.168.1.10:7000"
is_dev = len(sys.argv) > 1
if is_dev:
    print("Development")
else:
    print("Production")

# Timer con ritardo all'innesco, riarmabile
class MyTimer:
    def __init__(self, interval, callback):
        self.timer = None
        self.interval = interval
        self.callback = callback

    def start(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.interval, self.callback)
        self.timer.start()

# Callback del timer
def timer_callback():
    # Informo l'altro pc che ci sono nuovi dati
    try:
        requests.head(f"http://{dev_ip if is_dev else prod_ip}", timeout=2)
        print("Richiesta HEAD successo")
    except:
        print("Richiesta HEAD errore")


timer = MyTimer(2, timer_callback)

# Reagisce ai cambiamenti dei file
class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.src_path == f"{data_project_dir}PARTWIN3.TOT":
            timer.start()

event_handler = MyHandler()
observer = Observer()
observer.schedule(event_handler, data_project_dir, False)
observer.start()

# Handler per server, download dei file
class MyServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=data_project_dir, **kwargs)

httpd = http.server.HTTPServer(("0.0.0.0", 8000), MyServerHandler)

# Notifico che sono pronto
timer_callback()

print("Pronto")
httpd.serve_forever()

observer.stop()
observer.join()
