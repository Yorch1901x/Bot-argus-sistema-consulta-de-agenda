from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import urllib3
import re
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

LOGIN_URL = "https://sistema.grupoargus.co.cr/login.aspx"
AGENDA_URL = "https://sistema.grupoargus.co.cr/citas.aspx"
CRED = {
    "txt_login": "*******",
    "txt_password": "************",
    "cmd_ingresar": "Ingresar"
}

# --- HORAS VÁLIDAS ---
HORAS_VALIDAS = []
for h in range(7, 19):
    for m in (0, 30):
        sufijo = "a. m." if h < 12 else "p. m."
        hh = h if h <= 12 else h - 12
        HORAS_VALIDAS.append(f"{hh}:{m:02d} {sufijo}")

def normalizar_hora(hora):
    hora = hora.lower()
    hora = hora.replace("am", "a. m.").replace("pm", "p. m.")
    hora = hora.replace("a.m.", "a. m.").replace("p.m.", "p. m.")
    hora = re.sub(r"\s+", " ", hora.strip())
    return hora

def es_hora_valida(hora):
    return bool(re.search(r":00|:30", hora))

def obtener_disponibilidad(fecha=None):
    """
    Consulta la disponibilidad en el sistema real de Grupo Argus para la fecha indicada.
    """
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

    # --- FECHA A CONSULTAR ---
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise Exception("Formato de fecha inválido. Usa YYYY-MM-DD.")

    fecha_formateada = fecha_obj.strftime("%d/%m/%Y")

    # --- OBTENER ESTADO DE LA PÁGINA ---
    pagina = session.get(AGENDA_URL, verify=False)
    soup = BeautifulSoup(pagina.text, "html.parser")
    state_data = {tag["name"]: tag.get("value", "") for tag in soup.find_all("input", type="hidden")}

    # --- ARMAR PAYLOAD DE BÚSQUEDA CON FECHA ---
    # Esto simula presionar "Buscar" en la web
    payload = {
        **state_data,
        "ctl00$MainContent$txt_fecha": fecha_formateada,
        "ctl00$MainContent$cmd_buscar": "Buscar"
    }

    # --- PETICIÓN DE AGENDA ---
    agenda = session.post(AGENDA_URL, data=payload, verify=False)
    soup = BeautifulSoup(agenda.text, "html.parser")

    table = soup.find("table", {"id": "MainContent_grid_datos"}) or soup.find("table", class_="grid_age")
    if not table:
        raise Exception(f"No se encontró disponibilidad para la fecha {fecha_formateada}")

    # --- DETECTAR DOCTORES ---
    header = None
    for tr in table.find_all("tr"):
        texts = [td.get_text(strip=True) for td in tr.find_all("td")]
        if any("Dr." in t or "Examenes" in t or "Citas" in t for t in texts):
            header = tr
            break

    if not header:
        raise Exception("No se detectaron doctores en la tabla")

    cols = header.find_all("td")[1:]
    doctores = [td.get_text(strip=True) for td in cols]
    disponibles_por_doctor = {doc: [] for doc in doctores}
    rows = table.find_all("tr")
    active_rowspans = [0] * len(doctores)

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
                title = boton.get("title", "").strip()
                value = boton.get("value", "").strip()
                texto_boton = title if title else value
                if "Disponible" in texto_boton:
                    match = re.search(r"(\d{1,2}:\d{2}\s+[ap]\.\s*m\.)", texto_boton)
                    hora_encontrada = normalizar_hora(match.group(1)) if match else hora_actual
                    if not es_hora_valida(hora_encontrada):
                        continue
                    doctor_asignado = next((d for d in doctores if d in title), doctor_columna)
                    disponibles_por_doctor[doctor_asignado].append({
                        "fecha": fecha_formateada,
                        "hora": hora_encontrada,
                        "detalle": title or "Disponible"
                    })
            active_rowspans[col_index] = rowspan - 1
            col_index += 1

    return {
        "fecha": fecha_formateada,
        "disponibilidad": disponibles_por_doctor
    }

# --- ENDPOINT GENERAL ---
@app.route('/api/disponibilidad', methods=['GET'])
def disponibilidad_general():
    try:
        fecha = request.args.get("fecha")
        resultado = obtener_disponibilidad(fecha)
        return jsonify({
            "status": "success",
            "data": resultado
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT POR DOCTOR ---
@app.route('/api/disponibilidad/<doctor>', methods=['GET'])
def disponibilidad_por_doctor(doctor):
    try:
        fecha = request.args.get("fecha")
        resultado = obtener_disponibilidad(fecha)
        doctor = doctor.replace("_", " ")
        data = resultado["disponibilidad"]
        if doctor not in data:
            return jsonify({
                "status": "error",
                "message": f"No se encontró al doctor '{doctor}' en la fecha solicitada."
            }), 404
        return jsonify({
            "status": "success",
            "fecha": resultado["fecha"],
            "doctor": doctor,
            "disponibilidad": data[doctor]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- MAIN ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

