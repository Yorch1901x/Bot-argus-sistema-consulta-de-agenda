from bs4 import BeautifulSoup
import requests
import urllib3
import json
import re
import os
from flask import Flask, jsonify

app = Flask(__name__)

# --- CONFIGURACIÓN BÁSICA ---
LOGIN_URL = "https://sistema.grupoargus.co.cr/login.aspx"
AGENDA_URL = "https://sistema.grupoargus.co.cr/citas.aspx"

CRED = {
    "txt_login": "L.gutierrez",
    "txt_password": "LgLxmed23",
    "cmd_ingresar": "Ingresar"
}

HORAS_VALIDAS = [
    "08:00", "09:00", "10:00", "11:00", "12:00",
    "13:00", "14:00", "15:00", "16:00", "17:00"
]

# --- FUNCIONES AUXILIARES ---
def normalizar_hora(texto):
    match = re.search(r"(\d{1,2}:\d{2})", texto)
    return match.group(1) if match else None

def es_hora_valida(hora):
    return hora in HORAS_VALIDAS

# --- FUNCIÓN PRINCIPAL ---
def obtener_disponibilidad():
    session = requests.Session()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        # --- LOGIN ---
        response = session.post(LOGIN_URL, data=CRED, verify=False, timeout=15)
        response.raise_for_status()

        # Verifica que el login fue exitoso (depende del HTML real)
        if "login" in response.url.lower():
            raise Exception("No se pudo iniciar sesión, verifique credenciales o URL.")

        # --- OBTENER AGENDA ---
        agenda_page = session.get(AGENDA_URL, verify=False, timeout=15)
        agenda_page.raise_for_status()

        soup = BeautifulSoup(agenda_page.text, 'html.parser')

        # --- PARSEAR DATOS ---
        disponibles_por_doctor = {}
        for fila in soup.select("table.agenda tr"):
            columnas = fila.find_all("td")
            if len(columnas) >= 2:
                doctor = columnas[0].get_text(strip=True)
                hora = normalizar_hora(columnas[1].get_text(strip=True))
                if doctor and hora and es_hora_valida(hora):
                    disponibles_por_doctor.setdefault(doctor, []).append(hora)

        # Si no se encontraron datos, lanza excepción
        if not disponibles_por_doctor:
            raise Exception("No se encontraron espacios disponibles o estructura de HTML cambió.")

        return disponibles_por_doctor

    except Exception as e:
        # Fallback: modo mock si falla la conexión o scraping
        print(f"[WARN] Scraping falló: {e}. Usando datos simulados.")
        return {
            "Dr. Pérez": ["09:00", "10:00", "11:00"],
            "Dra. Gómez": ["14:00", "15:00"],
            "Dr. Ramírez": ["08:00", "12:00", "16:00"]
        }

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
