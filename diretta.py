import http.server
import requests
import os
import sys
from pypxlib import Table
import json
import datetime
import asyncio
import websockets
import threading
import logging

prod_ip = "http://192.168.0.10:7000"
dev_ip = "http://192.168.1.10:7000"

is_dev = len(sys.argv) > 1
if is_dev:
    print("Development")
    ip = dev_ip
else:
    print("Production")
    ip = prod_ip

files = ["TElenco.DB", "TNote.DB", "TRilev.DB", "LstSubH.dat", "LstSubV.dat"]
tables = {"TElenco.DB": None, "TNote.DB": None, "TRilev.DB": None}

points = None
last_points = None

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
            r = requests.get(f"{ip}/{file}", timeout=2)
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
    global points, last_points
    print("inizio ciclo")
    if tables["TRilev.DB"]:
        points = [{"Cognome": x["Cognome"], "Nome": x["Nome"], "Punti": 0, "CodSq": x["CodSq"], "Pet": x["Pet"], "Prog": x["Prog"]} for x in table_to_json(tables["TElenco.DB"])]
        points_tmp = dict()
        for row in tables["TRilev.DB"]:
            codice = row["Codice"]
            try:
                int(codice[1:3])
            except:
                continue
            if codice[3:4] == "A" and codice[5:6] == "#" or \
                codice[3:4] == "B" and codice[5:6] == "#" or \
                codice[3:4] == "S" and codice[5:6] == "#":
                if codice[0:3] not in points_tmp:
                    points_tmp[codice[0:3]] = 0
                points_tmp[codice[0:3]] = points_tmp[codice[0:3]] + 1
        last_points = []
        for i in range(len(tables["TRilev.DB"]) - 1, 0, -1):
            row = tables["TRilev.DB"][i]
            codice = row.Codice
            if codice[1:2] != "p":
                continue
            last_points.append(codice)
            if codice == "*p01:00" or codice == "ap00:01" or len(last_points) == 5:
                break
        print(points_tmp)
        print(last_points)
        for key in points_tmp:
            value = points_tmp[key]
            giocatore = next(filter(lambda g: g["Pet"] == int(key[1:3]) and ((g["CodSq"] == "0") == (key[0:1] == "*")), points), None)
            indice = points.index(giocatore)
            points[indice]["Punti"] = value
    else:
        points = None
        last_points = None
    with open("C:/Bolghera/luogo.txt", "w") as f:
        if tables["TNote.DB"] and tables["TNote.DB"][0].Citta:
            f.write(hex_to_string(tables["TNote.DB"][0].Citta))
        else:
            f.write("Non definito")
    print("fine ciclo")
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
    return json.dumps({
        "elenco": table_to_json(tables["TElenco.DB"]),
        "note": row_to_json(tables["TNote.DB"][0]),
        "punti": points,
        "last_points": last_points,
    })


class Handler(http.server.BaseHTTPRequestHandler):
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
except Exception as e:
    print(e)

print("Fermo server HTTP")

if th.is_alive():
    httpd.shutdown()
    th.join(timeout=3)