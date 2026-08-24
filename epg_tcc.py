import requests
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime, timedelta, timezone


# ============================================================
# CONFIGURACIÓN
# ============================================================

API = "https://www.tccvivo.com.uy/api/v1/navigation_filter/1575/filter/"


# ============================================================
# FECHA Y BLOQUES DE CONSULTA
# ============================================================

ahora_utc = datetime.now(timezone.utc)

dia = ahora_utc.replace(
    hour=0,
    minute=0,
    second=0,
    microsecond=0
)

bloques = [
    (dia, dia + timedelta(hours=12)),
    (dia + timedelta(hours=12), dia + timedelta(days=1))
]


# ============================================================
# GUARDAR CANALES Y EVENTOS
# ============================================================

todos_canales = {}


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

        canal_id = str(
            canal.get(
                "service_id",
                canal.get("id", "0")
            )
        )

        if canal_id not in todos_canales:

            todos_canales[canal_id] = canal

        else:

            todos_canales[canal_id].setdefault("events", [])

            todos_canales[canal_id]["events"].extend(
                canal.get("events", [])
            )


# ============================================================
# CREAR XMLTV
# ============================================================

tv = Element(
    "tv",
    generator_info_name="TCC EPG"
)

programas_guardados = set()


# ============================================================
# PROCESAR CANALES
# ============================================================

for canal_id, canal in todos_canales.items():

    localized = canal.get("localized", [])

    nombre = (
        localized[0].get("title", "Canal")
        if localized
        else canal.get("name", "Canal")
    )


    # --------------------------------------------------------
    # CANAL
    # --------------------------------------------------------

    ch = SubElement(
        tv,
        "channel",
        id=canal_id
    )

    dn = SubElement(
        ch,
        "display-name"
    )

    dn.text = nombre


    # --------------------------------------------------------
    # PROGRAMAS
    # --------------------------------------------------------

    for evento in canal.get("events", []):

        inicio = evento.get("emission_start")
        fin = evento.get("emission_end")

        if not inicio or not fin:
            continue


        # ----------------------------------------------------
        # CONVERTIR FECHAS
        # ----------------------------------------------------

        try:

            fecha_inicio = datetime.fromisoformat(
                inicio.replace("Z", "+00:00")
            )

            fecha_fin = datetime.fromisoformat(
                fin.replace("Z", "+00:00")
            )

        except ValueError:

            print(
                "Fecha inválida:",
                inicio,
                fin
            )

            continue


        # ----------------------------------------------------
        # IGNORAR PROGRAMAS YA TERMINADOS
        # ----------------------------------------------------

        if fecha_fin < ahora_utc:
            continue


        # ----------------------------------------------------
        # EVITAR DUPLICADOS
        # ----------------------------------------------------

        clave = (
            canal_id,
            inicio,
            fin
        )

        if clave in programas_guardados:
            continue

        programas_guardados.add(clave)


        # ----------------------------------------------------
        # CREAR PROGRAMME
        # ----------------------------------------------------

        prog = SubElement(
            tv,
            "programme",
            channel=canal_id,
            start=fecha_inicio.strftime(
                "%Y%m%d%H%M%S +0000"
            ),
            stop=fecha_fin.strftime(
                "%Y%m%d%H%M%S +0000"
            )
        )


        # ----------------------------------------------------
        # TÍTULO Y DESCRIPCIÓN
        # ----------------------------------------------------

        loc = evento.get("localized", [])

        titulo_texto = (
            loc[0].get(
                "title",
                "Sin información"
            )
            if loc
            else "Sin información"
        )

        descripcion_texto = (
            loc[0].get(
                "description",
                ""
            )
            if loc
            else ""
        )


        # TÍTULO

        title = SubElement(
            prog,
            "title",
            lang="es"
        )

        title.text = titulo_texto


        # DESCRIPCIÓN

        desc = SubElement(
            prog,
            "desc",
            lang="es"
        )

        desc.text = descripcion_texto or ""


        # ----------------------------------------------------
        # IMAGEN DEL PROGRAMA
        # ----------------------------------------------------
        # La API de TCC devuelve las imágenes dentro de:
        #
        # "images": [
        #     {
        #         "type": "FRM",
        #         "image_media": {
        #             "file": "//zpapi.zetatv.com.uy/..."
        #         }
        #     }
        # ]
        #
        # Buscamos específicamente la imagen FRM.
        # ----------------------------------------------------

        imagen_url = None

        imagenes = evento.get("images", [])

        # Primero buscar imagen FRM

        for imagen in imagenes:

            if imagen.get("type") == "FRM":

                image_media = imagen.get(
                    "image_media",
                    {}
                )

                imagen_url = image_media.get("file")

                if imagen_url:
                    break


        # Si no hay FRM, intentar usar cualquier imagen

        if not imagen_url and imagenes:

            for imagen in imagenes:

                image_media = imagen.get(
                    "image_media",
                    {}
                )

                imagen_url = image_media.get("file")

                if imagen_url:
                    break


        # ----------------------------------------------------
        # CONVERTIR // A HTTPS
        # ----------------------------------------------------

        if imagen_url:

            if imagen_url.startswith("//"):
                imagen_url = "https:" + imagen_url

            elif imagen_url.startswith("/"):
                imagen_url = (
                    "https://zpapi.zetatv.com.uy"
                    + imagen_url
                )


            # ------------------------------------------------
            # AGREGAR ICON AL XMLTV
            # ------------------------------------------------

            icon = SubElement(
                prog,
                "icon",
                src=imagen_url
            )


# ============================================================
# GUARDAR XML
# ============================================================

ElementTree(tv).write(
    "epg.xml",
    encoding="utf-8",
    xml_declaration=True
)


# ============================================================
# FINAL
# ============================================================

print()
print("==========================================")
print("EPG generado correctamente")
print("Canales:", len(todos_canales))
print("Programas:", len(programas_guardados))
print("Archivo: epg.xml")
print("==========================================")
