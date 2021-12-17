from pypxlib import Table
import datetime
import ffmpeg
import os
import shutil
import sys

if len(sys.argv) < 2:
    print("Inserire video input")
    exit()

video = sys.argv[1]

data_project_dir = "C:/Data Project/Data Volley 4/Data/"
video_dir = "V:/Ruggi/Videos/Bolghera/"
video_dir_tmp = video_dir + "tmp/"

rilev = Table(data_project_dir + "TRilev.DB")
elenco = Table(data_project_dir + "TElenco.DB")
note = Table(data_project_dir + "TNote.DB")


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


def crea_montaggio(**kwargs):
    try:
        shutil.rmtree(video_dir_tmp)
    except:
        pass
    os.mkdir(video_dir_tmp)
    counter = 0
    squadra = kwargs.get("squadra", False)
    numero = kwargs.get("numero", False)
    fond = kwargs.get("fond", False)
    esito = kwargs.get("esito", False)
    zonaP = kwargs.get("zonaP", False)
    start = kwargs.get("start", 0)
    end = kwargs.get("end", 0)
    set = kwargs.get("set", 0)
    nome = kwargs.get("nome", "video")
    max_counter = kwargs.get("max_counter", False)
    rot = kwargs.get("rot", False)
    aRot = kwargs.get("aRot", False)
    rice = kwargs.get("rice", False)
    fine_azione = kwargs.get("fine_azione", False)
    for i, value in enumerate(rilev):
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
        if fond and codice[3] != fond:
            continue
        if esito and codice[5] != esito:
            continue
        if zonaP and codice[9] != zonaP:
            continue
        if rot and value.ZPagg0 != rot:
            continue
        if aRot and value.ZPagg1 != aRot:
            continue
        if rice and rilev[i - 1].Codice[3] != "R":
            continue
        if rice and rice == "buona" and rilev[i - 1].Codice[5] not in "#+":
            continue
        if rice and rice == "cattiva" and rilev[i - 1].Codice[5] not in "!-":
            continue
        if fine_azione:
            i2 = i
            while True:
                codice2 = rilev[i2].Codice
                if codice2[1] == "p":
                    break
                i2 += 1
            t_fine_azione = rilev[i2].Millisec
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
                video_dir + video,
                ss=value.Millisec + start,
                t=t_fine_azione + end,
                hide_banner=None,
            )
        else:
            stream = ffmpeg.input(
                video_dir + video,
                ss=value.Millisec + start,
                to=t_fine_azione + end,
                hide_banner=None,
            )
        stream = ffmpeg.output(
            stream, video_dir_tmp + f"{nome}_{counter}.mp4", vcodec="copy"
        )
        ffmpeg.run(stream, cmd="V:/Ruggi/Videos/Programmi/ffmpeg")
        counter = counter + 1
    if counter == 0:
        return
    print("metto tutto assieme")
    with open(video_dir_tmp + "list.txt", "w") as f:
        for i in range(counter):
            f.write(f"file '{nome}_{i}.mp4'\n")
    stream = ffmpeg.input(
        video_dir_tmp + "list.txt", f="concat", safe="0", hide_banner=None
    )
    stream = ffmpeg.output(stream, video_dir + f"{nome}.mp4", vcodec="copy")
    print(ffmpeg.compile(stream))
    ffmpeg.run(stream, cmd="V:/Ruggi/Videos/Programmi/ffmpeg")
    shutil.rmtree(video_dir_tmp, ignore_errors=True)


# fmt: off
# Distribuzione su ricezione
crea_montaggio(squadra="*", numero="10", fond="E", rot="1", rice="buona", start=1, end=1, nome="Dist Rot1 Rice buona")
crea_montaggio(squadra="*", numero="10", fond="E", rot="2", rice="buona", start=1, end=1, nome="Dist Rot2 Rice buona")
crea_montaggio(squadra="*", numero="10", fond="E", rot="3", rice="buona", start=1, end=1, nome="Dist Rot3 Rice buona")
crea_montaggio(squadra="*", numero="10", fond="E", rot="4", rice="buona", start=1, end=1, nome="Dist Rot4 Rice buona")
crea_montaggio(squadra="*", numero="10", fond="E", rot="5", rice="buona", start=1, end=1, nome="Dist Rot5 Rice buona")
crea_montaggio(squadra="*", numero="10", fond="E", rot="6", rice="buona", start=1, end=1, nome="Dist Rot6 Rice buona")
crea_montaggio(squadra="*", numero="10", fond="E", rot="1", rice="cattiva", start=1, end=1, nome="Dist Rot1 Rice cattiva")
crea_montaggio(squadra="*", numero="10", fond="E", rot="2", rice="cattiva", start=1, end=1, nome="Dist Rot2 Rice cattiva")
crea_montaggio(squadra="*", numero="10", fond="E", rot="3", rice="cattiva", start=1, end=1, nome="Dist Rot3 Rice cattiva")
crea_montaggio(squadra="*", numero="10", fond="E", rot="4", rice="cattiva", start=1, end=1, nome="Dist Rot4 Rice cattiva")
crea_montaggio(squadra="*", numero="10", fond="E", rot="5", rice="cattiva", start=1, end=1, nome="Dist Rot5 Rice cattiva")
crea_montaggio(squadra="*", numero="10", fond="E", rot="6", rice="cattiva", start=1, end=1, nome="Dist Rot6 Rice cattiva")

# Attacchi avversari
crea_montaggio(squadra="a", fond="A", zonaP="9", nome="Attacco avversario Z1")
crea_montaggio(squadra="a", fond="A", zonaP="2", nome="Attacco avversario Z2")
crea_montaggio(squadra="a", fond="A", zonaP="3", nome="Attacco avversario Z3")
crea_montaggio(squadra="a", fond="A", zonaP="4", nome="Attacco avversario Z4")
crea_montaggio(squadra="a", fond="A", zonaP="7", nome="Attacco avversario Z5")
crea_montaggio(squadra="a", fond="A", zonaP="8", nome="Attacco avversario Z6")

# Montaggi per set
crea_montaggio(fond="S", set=1, fine_azione=True, nome="Primo set")
crea_montaggio(fond="S", set=2, fine_azione=True, nome="Secondo set")
crea_montaggio(fond="S", set=3, fine_azione=True, nome="Terzo set")
crea_montaggio(fond="S", set=4, fine_azione=True, nome="Quarto set")
crea_montaggio(fond="S", set=5, fine_azione=True, nome="Quinto set")

# Attacco avversario Zona 1 P
crea_montaggio(squadra="a", fond="A", zonaP="1", rot="1", nome="Attacco avversario Z1 P1")
crea_montaggio(squadra="a", fond="A", zonaP="1", rot="2", nome="Attacco avversario Z1 P2")
crea_montaggio(squadra="a", fond="A", zonaP="1", rot="3", nome="Attacco avversario Z1 P3")
crea_montaggio(squadra="a", fond="A", zonaP="1", rot="4", nome="Attacco avversario Z1 P4")
crea_montaggio(squadra="a", fond="A", zonaP="1", rot="5", nome="Attacco avversario Z1 P5")
crea_montaggio(squadra="a", fond="A", zonaP="1", rot="6", nome="Attacco avversario Z1 P6")

# Attacco avversario Zona 2 P
crea_montaggio(squadra="a", fond="A", zonaP="2", rot="1", nome="Attacco avversario Z2 P1")
crea_montaggio(squadra="a", fond="A", zonaP="2", rot="2", nome="Attacco avversario Z2 P2")
crea_montaggio(squadra="a", fond="A", zonaP="2", rot="3", nome="Attacco avversario Z2 P3")
crea_montaggio(squadra="a", fond="A", zonaP="2", rot="4", nome="Attacco avversario Z2 P4")
crea_montaggio(squadra="a", fond="A", zonaP="2", rot="5", nome="Attacco avversario Z2 P5")
crea_montaggio(squadra="a", fond="A", zonaP="2", rot="6", nome="Attacco avversario Z2 P6")

# Attacco avversario Zona 4 P
crea_montaggio(squadra="a", fond="A", zonaP="4", rot="1", nome="Attacco avversario Z4 P1")
crea_montaggio(squadra="a", fond="A", zonaP="4", rot="2", nome="Attacco avversario Z4 P2")
crea_montaggio(squadra="a", fond="A", zonaP="4", rot="3", nome="Attacco avversario Z4 P3")
crea_montaggio(squadra="a", fond="A", zonaP="4", rot="4", nome="Attacco avversario Z4 P4")
crea_montaggio(squadra="a", fond="A", zonaP="4", rot="5", nome="Attacco avversario Z4 P5")
crea_montaggio(squadra="a", fond="A", zonaP="4", rot="6", nome="Attacco avversario Z4 P6")

# fmt: on

rilev.close()
elenco.close()
note.close()
