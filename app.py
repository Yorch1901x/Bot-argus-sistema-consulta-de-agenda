from bs4 import BeautifulSoup
import requests
import urllib3
import json
import re
import os
from flask import Flask, jsonify
from flask_cors import CORS  # 👈 habilitar CORS para Vapi

# --- CONFIGURACIÓN FLASK ---
app = Flask(__name__)
CORS(app)  # 👈 Permite solicitudes desde cualquier origen (Vapi, navegador, etc.)

# --- CONFIGURACIÓN BÁSICA ---
LOGIN_URL = "https://sistema.grupoargus.co.cr/login.aspx"
AGENDA_URL = "https://sistema.grupoargus.co.cr/citas.aspx"

CRED = {
    "txt_login": "L.gutierrez",
    "txt_password": "LgLxmed23",
    "cmd_ingresar": "Ingresar"
}

# --- GENERAR HORAS VÁLIDAS ---
HORAS_VALIDAS = []
for h in range(7, 19):  # 7:00 a.m. a 6:30 p.m.
    for m in (0, 30):
        sufijo = "a. m." if h < 12 else "p. m."
        hh = h if h <= 12 else h - 12
        HORAS_VALIDAS.append(f"{hh}:{m:02d} {sufijo}")

# --- FUNCIONES AUXILIARES ---
def normalizar_hora(hora):
    hora = hora.lower()
    hora = hora.replace("am", "a. m.").replace("pm", "p. m.")
    hora = hora.replace("a.m.", "a. m.").replace("p.m.", "p. m.")
    hora = re.sub(r"\s+", " ", hora.strip())
    return hora

def es_hora_valida(hora):
    """Devuelve True si la hora termina en :00 o :30."""
    return bool(re.search(r":00|:30", hora))

# --- FUNCIÓN PRINCIPAL ---
def obtener_disponibilidad():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()

    # --- LOGIN ---
    r = session.get(LOGIN_URL, verify=False)
    soup = BeautifulSoup(r.text, "html.parser")
    hidden = {tag["name"]: tag.get("value", "") for tag in soup.find_all("input", type="hidden")}
    cred = CRED.copy()
    cred.update(hidden)

    resp = session.post(LOGIN_URL, data=cred, verify=False)
    if "citas" not in resp.text and "Cerrar Sesión" not in resp.text:
        raise Exception("No se pudo iniciar sesión en el sistema Argus")

    # --- OBTENER TABLA DE AGENDA ---
    agenda = session.get(AGENDA_URL, verify=False)
    soup = BeautifulSoup(agenda.text, "html.parser")
    table = soup.find("table", {"id": "MainContent_grid_datos"}) or soup.find("table", class_="grid_age")
    if not table:
        raise Exception("No se encontró la tabla de agenda en la página")

    # --- OBTENER ENCABEZADOS ---
    header = None
    for tr in table.find_all("tr"):
        texts = [td.get_text(strip=True) for td in tr.find_all("td")]
        if any("Dr." in t or "Examenes" in t or "Citas" in t for t in texts):
            header = tr
            break

    if not header:
        raise Exception("No se detectaron los encabezados de doctores")

    cols = header.find_all("td")[1:]
    doctores = [td.get_text(strip=True) for td in cols]

    disponibles_por_doctor = {doc: [] for doc in doctores}
    ocupado_horas = {doc: set() for doc in doctores}
    rows = table.find_all("tr")
    active_rowspans = [0] * len(doctores)

    # --- RECORRER FILAS ---
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) <= 1:
            continue

        hora_texto = normalizar_hora(tds[0].get_text(strip=True))
        if hora_texto not in HORAS_VALIDAS:
            continue

        hora_actual = hora_texto
        tds = tds[1:]
        col_index = 0

        for td in tds:
            while col_index < len(active_rowspans) and active_rowspans[col_index] > 0:
                active_rowspans[col_index] -= 1
                col_index += 1
            if col_index >= len(doctores):
                break

            doctor_columna = doctores[col_index]
            rowspan = int(td.get("rowspan", "1"))
            boton = td.find("input", {"type": "submit"})

            if boton:
                value = boton.get("value", "").strip()
                title = boton.get("title", "").strip()
                texto_boton = title if title else value

                if "Disponible" in texto_boton:
                    hora_del_boton = None
                    match_boton = re.search(r"(\d{1,2}:\d{2}\s+[ap]\.\s*m\.)", texto_boton)

                    if match_boton:
                        hora_del_boton = normalizar_hora(match_boton.group(1))
                        if not es_hora_valida(hora_del_boton):
                            continue
                    else:
                        hora_del_boton = hora_actual

                    doctor_asignado = None
                    for doc_key in doctores:
                        if doc_key in title:
                            doctor_asignado = doc_key
                            break

                    if doctor_asignado is None:
                        doctor_asignado = doctor_columna

                    if doctor_asignado in disponibles_por_doctor:
                        disponibles_por_doctor[doctor_asignado].append(f"{hora_actual} - {title}")

            active_rowspans[col_index] = rowspan - 1
            col_index += 1

    # --- FILTRAR RESULTADO FINAL ---
    disponibles_final = {
        doc: [d for d in lista if es_hora_valida(d.split(" - ")[0])]
        for doc, lista in disponibles_por_doctor.items()
    }

    return disponibles_final

# --- ENDPOINT API ---
@app.route('/api/disponibilidad', methods=['GET'])
def disponibilidad_endpoint():
    try:
        data = obtener_disponibilidad()
        return jsonify({
            "status": "success",
            "data": data,
            "message": "Disponibilidad obtenida correctamente."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al obtener disponibilidad: {str(e)}"
        }), 500

# --- MAIN ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
