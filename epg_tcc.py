import requests
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime, timedelta, timezone

API = "https://www.tccvivo.com.uy/api/v1/navigation_filter/1575/filter/"

ahora_utc = datetime.now(timezone.utc)
dia = ahora_utc.replace(hour=0, minute=0, second=0, microsecond=0)

bloques = [
    (dia, dia + timedelta(hours=12)),
    (dia + timedelta(hours=12), dia + timedelta(days=1))
]

tv = Element("tv", generator_info_name="TCC EPG")

for inicio, fin in bloques:
    start = inicio.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = fin.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (
        API
        + "?cable_operator=1"
        + "&emission_start=" + start
        + "&emission_end=" + end
        + "&format=json"
    )

    data = requests.get(url, timeout=30).json()

    for canal in data.get("results", []):
        canal_id = str(canal.get("service_id", canal.get("id", "0")))

        ch = SubElement(tv, "channel", id=canal_id)
        dn = SubElement(ch, "display-name")

        loc = canal.get("localized", [])
        dn.text = loc[0].get("title", "Canal") if loc else "Canal"

ElementTree(tv).write("epg.xml", encoding="utf-8", xml_declaration=True)
print("EPG generado correctamente")
