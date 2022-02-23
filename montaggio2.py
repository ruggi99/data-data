from pypxlib import Table
import datetime
import ffmpeg
import os
import shutil
import sys
import subprocess
import json
import configparser

data_root_dir = "C:/Data Project/Data Volley 4/"
data_project_dir = data_root_dir + "Data/"
data_seasons_dir = data_root_dir + "Seasons/"
video_dir = "V:/Ruggi/Videos/Bolghera/"
video_dir_tmp = video_dir + "tmp/"

rilev = Table(data_project_dir + "TRilev.DB")
elenco = Table(data_project_dir + "TElenco.DB")
note = Table(data_project_dir + "TNote.DB")

chiavi = list()
giocatori = dict()
battute = dict()
ricezioni = dict()
attacchi = dict()


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


config = configparser.ConfigParser()
config.read(data_root_dir + "dvwin.ini")
season = config["General"]["Season"]
filename = hex_to_string(note[0]["FilUltInc"])

config2 = configparser.ConfigParser(strict=False)
try:
    config2.read(data_seasons_dir + season + "/Scout/" + filename)
except configparser.ParsingError:
    pass
video = config2["3VIDEO"]["Camera0"]


def crea_montaggio(array, **kwargs):
    squadra = kwargs.get("squadra", False)
    numero = kwargs.get("numero", False)
    esito = kwargs.get("esito", False)
    zonaP = kwargs.get("zonaP", False)
    start = kwargs.get("start", 0)
    end = kwargs.get("end", 0)
    set = kwargs.get("set", 0)
    nome = kwargs.get("nome", "video")
    max_counter = kwargs.get("max_counter", False)
    rot = kwargs.get("rot", False)
    rice = kwargs.get("rice", False)
    fine_azione = kwargs.get("fine_azione", False)
    for chiave in chiavi:
        if chiave[0] != "*":
            continue
        counter = 0
        try:
            shutil.rmtree(video_dir_tmp)
        except:
            pass
        os.mkdir(video_dir_tmp)
        cognome = hex_to_string(giocatori[chiave].Cognome).replace("'", "")
        cognome = cognome[0].upper() + cognome[1:].lower()
        for i, value in enumerate(array[chiave]):
            if max_counter and counter >= max_counter:
                break
            codice = value.Codice
            try:
                int(codice[1:3])
            except:
                continue
            if squadra and codice[0] != squadra:
                continue
            if numero and codice[1:3] != numero:
                continue
            if esito and codice[5] != esito:
                continue
            if zonaP and codice[9] != zonaP:
                continue
            if rot and value.ZPagg0 != rot:
                continue
            if rice and rice == "buona" and rilev[i - 1].Codice[5] not in "#+":
                continue
            if rice and rice == "cattiva" and rilev[i - 1].Codice[5] not in "!-":
                continue
            if fine_azione:
                t_fine_azione = array[chiave + "p"][i]
            else:
                t_fine_azione = 4
            if set:
                if isinstance(set, list):
                    if value.Tempo not in set:
                        continue
                else:
                    if value.Tempo != set:
                        continue
            print(codice)
            if not fine_azione:
                stream = ffmpeg.input(
                    video,
                    ss=value.Millisec + start,
                    t=t_fine_azione + end,
                    hide_banner=None,
                )
            else:
                stream = ffmpeg.input(
                    video,
                    ss=value.Millisec + start,
                    to=t_fine_azione + end,
                    hide_banner=None,
                )
            stream = ffmpeg.output(
                stream, video_dir_tmp + f"{nome} {cognome}_{counter}.mp4", vcodec="copy"
            )
            print(ffmpeg.compile(stream))
            ffmpeg.run(stream, cmd="V:/Ruggi/Videos/Programmi/ffmpeg")
            counter = counter + 1
        if counter == 0:
            continue
        print("metto tutto assieme")
        with open(video_dir_tmp + "list.txt", "w") as f:
            for i in range(counter):
                f.write(f"file '{nome} {cognome}_{i}.mp4'\n")
        stream = ffmpeg.input(
            video_dir_tmp + "list.txt", f="concat", safe="0", hide_banner=None
        )
        stream = ffmpeg.output(
            stream, video_dir + f"{nome} {cognome}.mp4", vcodec="copy"
        )
        print(ffmpeg.compile(stream))
        ffmpeg.run(stream, cmd="V:/Ruggi/Videos/Programmi/ffmpeg")
        shutil.rmtree(video_dir_tmp, ignore_errors=True)
        # exit()


for value in elenco:
    numero = ("0" if value.Pet < 10 else "") + str(value.Pet)
    chiave = f"{'*' if value.CodSq == '0' else 'a'}{numero}"
    chiavi.append(chiave)
    giocatori[chiave] = value
    battute[chiave] = list()
    battute[chiave + "p"] = list()
    ricezioni[chiave] = list()
    attacchi[chiave] = list()

for i in range(len(rilev)):
    value = rilev[i]
    codice = value.Codice
    try:
        int(codice[1:3])
    except:
        continue
    chiave = codice[0:3]
    if codice[3] == "S":
        i2 = i
        while True:
            codice2 = rilev[i2].Codice
            if codice2[1] == "p":
                break
            i2 += 1
        battute[chiave].append(value)
        battute[chiave + "p"].append(rilev[i2].Millisec)
    elif codice[3] == "R":
        ricezioni[chiave].append(value)
    elif codice[3] == "A":
        attacchi[chiave].append(value)

# Controllo che sia un h264
streams = subprocess.run(
    ["V:/Ruggi/Videos/Programmi/ffprobe", "-show_streams", "-of", "json", video],
    capture_output=True,
    text=True,
)
streams = json.loads(streams.stdout)
if streams["streams"][0]["codec_name"] != "h264":
    print("Codec sbagliato")
    exit(1)

# Battuta per giocatore
crea_montaggio(battute, start=0, end=1, nome="Battuta")

crea_montaggio(ricezioni, start=1, end=1, nome="Ricezione")

crea_montaggio(attacchi, nome="Attacco")

print("\x1b[32mSuccesso!\x1b[0m")

rilev.close()
elenco.close()
note.close()
