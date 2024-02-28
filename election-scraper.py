import requests
from bs4 import BeautifulSoup
import csv
import sys
import re

def tabulky_na_url(url):
    odpoved = requests.get(url)
    polivka = BeautifulSoup(odpoved.content, 'html.parser')
    tabulky = polivka.find_all("table")
    return tabulky

#získání dat z tabulek v hlavním url
def ziskani_urls_z_dat_tabulek(tabulky):
    odkazy=[]
    for tabulka in tabulky:
        for odkaz in tabulka.find_all("a",href=True):
            odkazy.append(odkaz["href"])
    return odkazy

#scrapování politických stran z dat tabulek v odkazech
def vypis_jmena(tabulky:BeautifulSoup, jmeno_tagu:str="td"):
    strany=[]
    for tabulka in tabulky:
        for odkazz in tabulka.find_all(jmeno_tagu,{"class":"overflow_name"}):
            strany.append(odkazz)
    return strany

#registered
def vypis_pocet_registrovanych(tabulky_seznamu: list, jmeno_tagu: str = "td"):
    registered = []
    for tabulky in tabulky_seznamu:
        for tabulka in tabulky:
            registered.extend(tabulka.find_all(jmeno_tagu, {"class": "cislo", "headers": "sa2"}))
    return [int(re.sub(r'\D', '', data.text)) for data in registered if data.text]

#envelopes
def vypis_pocet_obalek(tabulky_seznamu: list, jmeno_tagu: str = "td"):
    envelopes = []
    for tabulky in tabulky_seznamu:
        for tabulka in tabulky:
            envelopes.extend(tabulka.find_all(jmeno_tagu, {"class": "cislo", "headers": "sa5"}))
    return [int(re.sub(r'\D', '', data.text)) for data in envelopes if data.text]
#valid
def vypis_pocet_platnych(tabulky_seznamu: list, jmeno_tagu: str = "td"):
    valid = []
    for tabulky in tabulky_seznamu:
        for tabulka in tabulky:
            valid.extend(tabulka.find_all(jmeno_tagu, {"class": "cislo", "headers": "sa6"}))
    return [int(re.sub(r'\D', '', data.text)) for data in valid if data.text]
#celkem hlasů pro stranu
def vypis_pocet_hlasu_pro_strany(tabulky_seznamu: list, jmeno_tagu: str, headers: str):
    hlasy = []
    for tabulky in tabulky_seznamu:
        for tabulka in tabulky:
            hlasy.extend(tabulka.find_all(jmeno_tagu, {"class": "cislo", "headers": headers}))
    return [int(re.sub(r'\D', '', data.text)) for data in hlasy if data.text]

def main():
    if len(sys.argv) <3:
        print("CHYBA: ,musíte zadat alespoň dva argumenty: URL a název CSV souboru")
    hlavni_url = sys.argv[1]

    print(f"STAHUJI DATA Z VYBRANÉHO URL:", hlavni_url)
    
    #získání jedinečných odkazů z tabulek v hlavním url. (koncových tabulek, které mají 
    #sečtené hlasy všech okrsků pomocí výberu v inspekci "vyber" ) + vytvoření unikátního seznamu bez duplicit   
    data_z_tabulek_hlavni_url = tabulky_na_url(hlavni_url)
    urls = ziskani_urls_z_dat_tabulek(data_z_tabulek_hlavni_url)
    odkazy_s_vyber= filter(lambda udaj: "vyber" in udaj, urls)
    unikatni_odkazy_s_vyber= []
    [unikatni_odkazy_s_vyber.append(x) for x in odkazy_s_vyber if x not in unikatni_odkazy_s_vyber]
    
    #vytvoření listu celých odkazů na původním url
    odkazy_list=["https://volby.cz/pls/ps2017nss/" + odkaz for odkaz in unikatni_odkazy_s_vyber]

    #získání dat z odkazů v tabulkách hlavního url
    data_z_odkazu=[]
    for cely_odkaz in odkazy_list:
        data_z_odkazu.append(tabulky_na_url(cely_odkaz))
        
    #hlava csv souboru + přidání vyscrapovaných politických stran do hlavy
    seznam_stran = vypis_jmena(data_z_odkazu[0])
    hlava = ["Code", "Location", "Registered", "Envelopes", "Valid"] #zde je uložená hlava
    #připravená do csv
    for pol_strana in (seznam_stran):
        hlava.append(f"{pol_strana.text}")
    
    #takto si vypíšu jména okrsků
    jmena_okrsku = vypis_jmena(data_z_tabulek_hlavni_url)
    jmena_okrsku_hotova=[]    #zde jsou uložené jména okrsků připravené do csv
    for jmeno_okrsku in (jmena_okrsku):
        jmena_okrsku_hotova.append(f"{jmeno_okrsku.text}")

    #takto vypíšu kódy
    kody_z_url=[] #zde jsou uložené kódy okrsků
    regex = r"xobec=(\d+)"
    for url in unikatni_odkazy_s_vyber:
        matches= re.findall(regex,url)
        kody_z_url.extend(matches)
        
    registrovana_cisla=vypis_pocet_registrovanych(data_z_odkazu)#zde jsou uložena čísla počtů registrovaných voličů
    envelopes_cisla=vypis_pocet_obalek(data_z_odkazu)#zde jsou uložena čísla počtů obálek
    valid_cisla=vypis_pocet_platnych(data_z_odkazu)#zde jsou uložena čísla počtů platných hlasů
    
    hlasy1hotovo = vypis_pocet_hlasu_pro_strany(data_z_odkazu, "td", "t1sa2 t1sb3")
    hlasy2hotovo = vypis_pocet_hlasu_pro_strany(data_z_odkazu, "td", "t2sa2 t2sb3")

    csv_file = sys.argv[2]
    index1 = int(len(hlasy1hotovo)/ len(kody_z_url))
    index2 = int(len(hlasy2hotovo)/ len(kody_z_url))

    print(f"UKLADAM DO SOUBORU:", csv_file)

    #spuštění vpisování získaných údajů do cvs souboru   
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(hlava)    
        for items in zip(kody_z_url, jmena_okrsku_hotova, registrovana_cisla, envelopes_cisla, valid_cisla, *([hlasy1hotovo[i::index1] for i in range(index1)] + [hlasy2hotovo[i::index2] for i in range(index2)])):
            writer.writerow(items)

    print(f"UKONČUJI",sys.argv[0])
if __name__ == "__main__":
    main()
