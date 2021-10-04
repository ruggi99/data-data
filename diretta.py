import http.server
import requests
import os
from pypxlib import Table
import json
import datetime
import asyncio
import websockets
import threading
import logging

files = ["TElenco.DB", "TNote.DB", "TRilev.DB", "LstSubH.dat", "LstSubV.dat"]
tables = {"TElenco.DB": None, "TNote.DB": None, "TRilev.DB": None}

def open_tables():
    for table in tables:
        if os.path.exists(os.path.expanduser("~/") + table):
            tables[table] = Table(os.path.expanduser("~/") + table)
        else:
            tables[table] = None

def download_files():
    # Download dei files
    # Aggiornamento variabili
    for table in tables:
        if tables[table] is not None:
            tables[table].close()
    print("Comincio download files")
    for file in files:
        try:
            r = requests.get(f"http://192.168.1.10:8000/{file}", timeout=2)
        except:
            try:
                os.remove(os.path.expanduser("~/") + file)
            except:
                pass
            continue
        # Se non esiste il file, ne viene creato uno vuoto   
        with open(os.path.expanduser("~/") + file, "wb") as f:
            if r.status_code == 200:
                f.write(r.content)
    open_tables()
    print("Download file completato")

# paths = ["/punteggio"]

def row_to_json(row):
    obj = {}
    for field_name in row._table.fields:
        value = row[field_name]
        if value is None:
            continue
        if isinstance(value, datetime.time):
            obj[field_name] = value.isoformat()
        elif isinstance(value, datetime.date):
            obj[field_name] = value.isoformat()
        elif isinstance(value, bytes):
            obj[field_name] = value.decode()
        elif isinstance(value, str) and value[0:1] == "\x0f":
            obj[field_name] = hex_to_string(value)
        else:
            obj[field_name] = row[field_name]
    return obj


def table_to_json(table):
    if table is None:
        return None
    arr = []
    for row in table:
        arr.append(row_to_json(row))
    return arr


def hex_to_string(hex):
    arr = []
    for i in range(2, len(hex), 2):
        arr.append(chr(int(hex[i : i + 2], 16)))
    return "".join(arr)

def punteggio():
    if tables["TElenco.DB"] is None or tables["TNote.DB"] is None:
        return json.dumps(None)
    return json.dumps({"elenco": table_to_json(tables["TElenco.DB"]), "note": row_to_json(tables["TNote.DB"][0])})


class Handler(http.server.BaseHTTPRequestHandler):
    # def do_GET(self):
    #     if not self.path in paths:
    #         self.send_error(404)
    #         print(f"Path non riconosciuto - {self.path}")
    #         return
    #     self.send_response(200)
    #     self.send_header('Access-Control-Allow-Origin', '*')
    #     self.send_header("Content-type", "application/json")
    #     self.end_headers()
    #     if self.path == "/punteggio":
    #         self.wfile.write(json.dumps({"elenco": table_to_json(tables["TElenco.DB"]), "note": row_to_json(tables["TNote.DB"][0])}).encode())
    #     print("Messaggio di controllo")
    def do_HEAD(self):
        print("HEAD", self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.flush()
        print("Risposta richiesta HEAD")
        download_files()
        print("Clienti collegati:", len(CLIENTS))
        websockets.broadcast(CLIENTS.copy(), punteggio())

httpd = http.server.HTTPServer(("0.0.0.0", 8000), Handler)

# Fa il download e apre i file automaticamente
download_files()

for table in tables:
    if tables[table] is None:
        print(f"{table} non esistente")

CLIENTS = set()

async def handle(websocket, path):
    CLIENTS.add(websocket)
    print("Nuovo cliente")
    await websocket.send(punteggio())
    try:
        await websocket.wait_closed()
    except:
        pass
    CLIENTS.remove(websocket)

async def main():
    async with websockets.serve(handle, "0.0.0.0", 8500):
        await asyncio.Future()

def serve_forever():
    print("Server HTTP attivo")
    httpd.serve_forever()

th = threading.Thread(target=serve_forever)
th.start()

logging.basicConfig(level=logging.INFO)

print("Server Websocket attivo")
try:
    asyncio.run(main())
except:
    pass

print("Fermo server HTTP")

if th.is_alive():
    httpd.shutdown()
    th.join(timeout=3)