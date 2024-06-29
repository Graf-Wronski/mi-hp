import pymongo
from datetime import datetime
from collections import OrderedDict
from .config import *

#from .util_logging import logger

# Connect to MongoDB
try:
    cluster = pymongo.MongoClient("mongodb://127.0.0.1:27017")
    mongo_db_vvz = cluster["vvz"]
    vvz_anforderung = mongo_db_vvz["anforderung"]
    vvz_anforderungkategorie = mongo_db_vvz["anforderungkategorie"]
    vvz_code = mongo_db_vvz["code"]
    vvz_codekategorie = mongo_db_vvz["codekategorie"]
    vvz_gebaeude = mongo_db_vvz["gebaeude"]
    vvz_rubrik = mongo_db_vvz["rubrik"]
    vvz_modul = mongo_db_vvz["modul"]
    vvz_person = mongo_db_vvz["person"]
    vvz_raum = mongo_db_vvz["raum"]
    vvz_semester = mongo_db_vvz["semester"]
    vvz_studiengang = mongo_db_vvz["studiengang"]
    vvz_terminart = mongo_db_vvz["terminart"]
    vvz_veranstaltung = mongo_db_vvz["veranstaltung"]
except:
    pass
    # logger.warning("No connection to Database 1")

# returns 
# a list of category shortnames (cats_kurzname), 
# a dictionary how to translate them into full names (names_dict), 
# a dict with the shortnames as keys, where each value is a list of triples (id, q, a), which contains the information for each question in each category (qa_pairs). 
# recall that category and qa come with a variable rang: int, which serves to order the categories and qa-pairs. 

def get_showanmeldung(studiengang):
    year = datetime.now().year
    date_format = '%d.%m.'
    res = False
    for b in bewerbungsdaten[studiengang]:
        loc_start = datetime.strptime(b["start"], date_format)
        loc_start = datetime(year, loc_start.month, loc_start.day)
        loc_end = datetime.strptime(b["end"], date_format)
        loc_end = datetime(year, loc_end.month, loc_end.day)
        if loc_start < datetime.now() and datetime.now() < loc_end:
            res = True
    return res

def get_showsemester(shortname):
    # Gibt es ein sichtbares Semester mit shortname?
    b = vvz_semester.find_one({"kurzname": shortname, "hp_sichtbar": True })
    return (b != None)

def get_current_semester_kurzname():
    if datetime.now().month < 4:
        res = f"{datetime.now().year-1}WS"
    elif 3 < datetime.now().month and datetime.now().month < 11:
        res = f"{datetime.now().year}SS"
    else:
        res = f"{datetime.now().year}WS"
    return res

def next_semester_kurzname(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    return f"{a+1}SS" if b == "WS" else f"{a}WS"

def semester_name_de(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    c = f"/{a+1}" if b == "WS" else ""
    return f"{'Wintersemester' if b == 'WS' else 'Sommersemester'} {a}{c}"

def semester_name_en(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    c = f"/{a+1}" if b == "WS" else ""
    return f"{'Winter term' if b == 'WS' else 'Summer term'} {a}{c}"

def get_html(raum_id):
    r = vvz_raum.find_one({ "_id": raum_id})
    g = vvz_gebaeude.find_one({ "_id": r["gebaeude"]})
    gurl = g["url"]
    if gurl == "":
        raum = ", ".join([r["name_de"], g["name_de"]])
    else:
        raum = ", ".join([r['name_de'], f"<a href = '{gurl}'>{g['name_de']}</a>"])
    return raum

def vorname_name(person_id):
    p = vvz_person.find_one({"_id": person_id})
    return f"{p['vorname']} {p['name']}"

# Die Funktion fasst zB Mo, 8-10, HS Rundbau, Albertstr. 21 \n Mi, 8-10, HS Rundbau, Albertstr. 21 \n 
# zusammen in
# Mo, Mi, 8-10, HS Rundbau, Albertstr. 21 \n Mi, 8-10, HS Rundbau, Albertstr. 21
def make_raumzeit(veranstaltung):
    res = []
    for termin in veranstaltung["woechentlicher_termin"]:
        ta = vvz_terminart.find_one({"_id": termin['key']})
        if ta["hp_sichtbar"]:
            ta = ta["name_de"]
            if termin['wochentag'] !="":
                # key, raum, zeit, person, kommentar
                key = f"{ta}:" if ta != "" else ""
                # Raum und Gebäude mit Url, zB Hs II.
                r = vvz_raum.find_one({ "_id": termin["raum"]})
                raum = get_html(r["_id"])
                # zB Vorlesung: Montag, 8-10 Uhr, HSII, Albertstr. 23a
                if termin['start'] is not None:
                    zeit = f"{str(termin['start'].hour)}{': '+str(termin['start'].minute) if termin['start'].minute > 0 else ''}"
                    if termin['ende'] is not None:
                        zeit = zeit + f"-{str(termin['ende'].hour)}{': '+str(termin['ende'].minute) if termin['ende'].minute > 0 else ''}"
                    zeit = zeit + " Uhr"
                else:
                    zeit = ""
                # zB Mo, 8-10
                tag = weekday[termin['wochentag']]
                # person braucht man, wenn wir dann die Datenbank geupdated haben.
                #person = ", ".join([f"{vvz_person.find_one({"_id": x})["vorname"]} {vvz_person.find_one({"_id": x})["name"]}"for x in termin["person"]])
                kommentar = rf"\newline{termin['kommentar']}" if termin['kommentar'] != "" else ""
                new = [key, tag, zeit, raum, kommentar]
                if key in [x[0] for x in res]:
                    new.pop(0)
                    i = [x[0] for x in res].index(key)
                    res[i] = (res[i] + new)
                    res[i].reverse()
                    res[i] = list(OrderedDict.fromkeys(res[i]))
                    res[i].reverse()
                else:
                    res.append(new)
    for termin in veranstaltung["einmaliger_termin"]:
        ta = vvz_terminart.find_one({"_id": termin['key']})
        if ta["hp_sichtbar"]:
            ta = ta["name_de"]
            # Raum und Gebäude mit Url.
            raeume = list(vvz_raum.find({ "_id": { "$in": termin["raum"]}}))
            raum = ", ".join([get_html(r["_id"]) for r in raeume])
            # zB Vorlesung: Montag, 8-10, HSII, Albertstr. 23a
            if termin['enddatum'] is None:
                termin['enddatum'] = termin['startdatum']
            if termin['startdatum'] is not None:
                startdatum = termin['startdatum'].strftime("%d.%m.")
                if termin['startdatum'] != termin['enddatum']:
                    enddatum = termin['enddatum'].strftime("%d.%m.")
                    datum = " bis ".join([startdatum, enddatum]) if startdatum != enddatum else startdatum
                else:
                    datum = startdatum
            else:
                datum = ""
            if termin['startzeit'] is not None:
                zeit = f"{str(termin['startzeit'].hour)}{': '+str(termin['startzeit'].minute) if termin['startzeit'].minute > 0 else ''}"
                if termin['endzeit'] is not None:
                    zeit = zeit + f"-{str(termin['endzeit'].hour)}{': '+str(termin['endzeit'].minute) if termin['endzeit'].minute > 0 else ''}"
                zeit = zeit + " Uhr"
            else:
                zeit = ""
            # person braucht man, wenn wir dann die Datenbank geupdated haben.
            # person = ", ".join([f"{vvz_person.find_one({"_id": x})["vorname"]} {vvz_person.find_one({"_id": x})["name"]}"for x in termin["person"]])
            kommentar = rf"{termin['kommentar']}" if termin['kommentar'] != "" else ""
            new = [ta, datum, zeit, raum, kommentar]
            res.append(new)
    res = [f"{x[0]} {(', '.join([z for z in x if z !='' and x.index(z)!=0]))}" for x in res]
    return res

def make_codes(sem_id, veranstaltung_id):
    res = ""
    codekategorie_list = [x["_id"] for x in list(vvz_codekategorie.find({"semester": sem_id, "hp_sichtbar": True}))]
    v = vvz_veranstaltung.find_one({"_id": veranstaltung_id})
    code_list = [vvz_code.find_one({"_id": c, "codekategorie": {"$in": codekategorie_list}}) for c in v["code"]]
    code_list = [x for x in code_list if x is not None]
    if len(code_list)>0:
        res = ", ".join([c["name"] for c in code_list])
    return res

def get_data(sem_shortname):
    sem_id = vvz_semester.find_one({"kurzname": sem_shortname})["_id"]

    rubriken = list(vvz_rubrik.find({"semester": sem_id, "hp_sichtbar": True}, sort=[("rang", pymongo.ASCENDING)]))

    codekategorie = list(vvz_codekategorie.find({"semester": sem_id, "hp_sichtbar": True}, sort=[("rang", pymongo.ASCENDING)]))
    codes = list(vvz_code.find({"semester": sem_id, "codekategorie": { "$in" : [c["_id"] for c in codekategorie] }}, sort=[("rang", pymongo.ASCENDING)]))
    #print(codes)

    data = {}
    data["semester"] = vvz_semester.find_one({"kurzname": sem_shortname})
    data["rubrik"] = []
    data["code"] = []

    for code in codes:
        if vvz_veranstaltung.find_one({"semester": sem_id, "code" : { "$elemMatch" : { "$eq": code["_id"]}}}):
            code_dict = {}
            code_dict["name"] = code["name"]
            code_dict["beschreibung"] = code["beschreibung_de"]
            data["code"].append(code_dict)
    print(data["code"])

    for rubrik in rubriken:
        r_dict = {}
        r_dict["titel"] = rubrik["titel_de"]
        r_dict["untertitel"] = rubrik["untertitel_de"]
        r_dict["prefix"] = rubrik["prefix_de"]
        r_dict["suffix"] = rubrik["suffix_de"]
        # print(r_dict["titel"])
        r_dict["veranstaltung"] = []
        veranstaltungen = list(vvz_veranstaltung.find({"rubrik": rubrik["_id"], "hp_sichtbar" : True}, sort=[("rang", pymongo.ASCENDING)]))
        for veranstaltung in veranstaltungen:
            v_dict = {}
            v_dict["code"] = make_codes(sem_id, veranstaltung["_id"])            
            v_dict["titel"] = veranstaltung["name_de"]
            v_dict["kommentar"] = veranstaltung["kommentar_html_de"]
            v_dict["link"] = veranstaltung["url"]
            v_dict["dozent"] = ", ".join([vorname_name(x) for x in veranstaltung["dozent"]])
            v_dict["assistent"] = ", ".join([vorname_name(x) for x in veranstaltung["assistent"]])
            # raumzeit ist der Text, der unter der Veranstaltung steht.
            # print(v_dict["titel"])
            v_dict["raumzeit"] = make_raumzeit(veranstaltung)
            r_dict["veranstaltung"].append(v_dict)

        data["rubrik"].append(r_dict)
        #print(data)
    return data

