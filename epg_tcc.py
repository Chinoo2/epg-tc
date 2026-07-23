import requests
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime, timedelta, timezone

API = "https://www.tccvivo.com.uy/api/v1/navigation_filter/1575/filter/"

ahora = datetime.now(timezone.utc)
dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

bloques = [
    (dia, dia + timedelta(hours=12)),
    (dia + timedelta(hours=12), dia + timedelta(days=1))
]

tv = Element("tv", generator_info_name="TCC EPG")

for inicio, fin in bloques:
    start = inicio.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = fin.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (
        f"{API}?cable_operator=1"
        f"&emission_start={start}"
        f"&emission_end={end}"
        "&format=json"
    )

    print("Consultando:", url)

    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    for canal in data.get("results", []):
        canal_id = str(canal.get("service_id", canal.get("id", "0")))

        ch = SubElement(tv, "channel", id=canal_id)
        dn = SubElement(ch, "display-name")

        loc = canal.get("localized", [])
        nombre = loc[0].get("title", "Canal") if loc else "Canal"
        dn.text = nombre

ElementTree(tv).write("epg.xml", encoding="utf-8", xml_declaration=True)

print("EPG generado correctamente")
