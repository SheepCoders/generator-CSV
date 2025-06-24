import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup  # Do czyszczenia HTML

# Stałe
DOWNLOAD_DIR = "xml_downloads"
CSV_DIR = "csv_exports"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

# Kolumny CSV
COLUMNS = [
    "produkt_id", "produkt_nazwa", "ilosc", "produkt_ean", "produkt_sku", "kategoria_nazwa", "cena", "stawka_vat", "waga",
    "opis", "opis_dodatkowy_1", "opis_dodatkowy_2", "opis_dodatkowy_3", "opis_dodatkowy_4",
    "zdjecie", "zdjecie_dodatkowe_1", "zdjecie_dodatkowe_2", "zdjecie_dodatkowe_3", "zdjecie_dodatkowe_4",
    "zdjecie_dodatkowe_5", "zdjecie_dodatkowe_6", "zdjecie_dodatkowe_7", "zdjecie_dodatkowe_8",
    "zdjecie_dodatkowe_9", "zdjecie_dodatkowe_10", "zdjecie_dodatkowe_11", "zdjecie_dodatkowe_12",
    "zdjecie_dodatkowe_13", "zdjecie_dodatkowe_14", "zdjecie_dodatkowe_15", "producent_nazwa"
]

# Źródła XML
SOURCES = {
    "togo": {
        "url": "https://hurt.togo.com.pl/xmlapi/1/3/utf8/1046ea66-fd78-42d5-b9b6-50814c795b4f",
        "headers": {},
    },
    "kolba": {
        "url": "https://b2b.kolba.pl/assets/default/integrations/instance/megaimport/KOLBAB2B.xml",
        "headers": {
            "User-Agent": "Mozilla/5.0"
        },
    }
}

# Pobierz i zapisz XML
def download_xml(name, url, headers):
    path = os.path.join(DOWNLOAD_DIR, f"{name}.xml")
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path

# Funkcja do wyciągania czystego tekstu z HTML
def clean_html(description):
    soup = BeautifulSoup(description, "html.parser")
    return soup.get_text(separator=" ").strip()

# Przetwarzanie TOGO
def parse_togo(path):
    tree = ET.parse(path)
    root = tree.getroot()
    products = []

    for product in root.findall("product"):
        p = dict.fromkeys(COLUMNS, "")
        p["produkt_id"] = product.findtext("id")
        p["produkt_nazwa"] = product.findtext("name")
        p["ilosc"] = product.findtext("qty") or "0"
        p["produkt_ean"] = product.findtext("ean")
        p["produkt_sku"] = product.findtext("sku")
        p["kategoria_nazwa"] = ";".join(cat.text or "" for cat in product.find("categories").findall("category"))
        p["cena"] = product.findtext("retailPriceGross")
        vat = product.findtext("vat")
        p["stawka_vat"] = f"{vat}%" if vat else ""
        p["waga"] = product.findtext("weight")
        
        # Czyszczenie opisu (usuwanie HTML)
        opis = product.findtext("desc")
        p["opis"] = clean_html(opis) if opis else ""
        
        p["producent_nazwa"] = product.findtext("brand")

        # Zdjęcia
        photos = [photo.text for photo in product.find("photos").findall("photo")]
        for i in range(16):
            col = "zdjecie" if i == 0 else f"zdjecie_dodatkowe_{i}"
            p[col] = photos[i] if i < len(photos) else ""

        products.append(p)
    return products

# Przetwarzanie KOLBA
def parse_kolba(path):
    tree = ET.parse(path)
    root = tree.getroot()
    products = []

    for produkt in root.findall("produkt"):
        base = dict.fromkeys(COLUMNS, "")
        base["produkt_id"] = produkt.findtext("id")
        base["produkt_nazwa"] = produkt.findtext("nazwa")
        base["produkt_sku"] = produkt.findtext("symbol")
        base["produkt_ean"] = produkt.findtext("ean")
        base["opis"] = produkt.findtext("dlugi_opis")
        base["cena"] = produkt.findtext("cena_brutto_hurt")
        base["stawka_vat"] = "23%"
        base["ilosc"] = produkt.findtext("na_magazynie") or "0"
        base["waga"] = ""  # Brak w XML

        # Zdjęcia
        zdj = produkt.find("zdjecia")
        if zdj is not None:
            photos = [z.text for z in zdj.findall("zdjecie")]
        else:
            photos = []
        for i in range(16):
            col = "zdjecie" if i == 0 else f"zdjecie_dodatkowe_{i}"
            base[col] = photos[i] if i < len(photos) else ""

        # Producent z atrybutu
        atrybuty = produkt.find("atrybuty")
        if atrybuty is not None:
            for atr in atrybuty.findall("atrybut"):
                if atr.attrib.get("nazwa") == "Producent":
                    base["producent_nazwa"] = atr.text

        # Warianty jako osobne produkty
        warianty = produkt.find("warianty")
        if warianty is not None and len(warianty) > 0:
            for wariant in warianty.findall("wariant"):
                p = base.copy()
                p["produkt_id"] = wariant.findtext("id")
                p["produkt_nazwa"] = wariant.findtext("nazwa") or base["produkt_nazwa"]
                p["produkt_sku"] = wariant.findtext("symbol") or base["produkt_sku"]
                p["produkt_ean"] = wariant.findtext("ean") or base["produkt_ean"]
                p["cena"] = wariant.findtext("cena_brutto_hurt") or base["cena"]
                p["ilosc"] = wariant.findtext("na_magazynie") or base["ilosc"]
                products.append(p)
        else:
            products.append(base)

    return products

# Uruchomienie
def main():
    for name, info in SOURCES.items():
        print(f"Pobieram {name}...")
        xml_path = download_xml(name, info["url"], info["headers"])

        if name == "togo":
            data = parse_togo(xml_path)
        elif name == "kolba":
            data = parse_kolba(xml_path)
        else:
            continue

        df = pd.DataFrame(data, columns=COLUMNS)
        df.to_csv(os.path.join(CSV_DIR, f"{name}.csv"), index=False, sep=";", quoting=1)
        print(f"{name}.csv zapisany")

if __name__ == "__main__":
    main()
