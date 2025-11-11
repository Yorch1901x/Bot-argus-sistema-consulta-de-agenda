from bs4 import BeautifulSoup
import requests
import urllib3
import json
import re
import os
from flask import Flask, jsonify

app = Flask(__name__)

# --- CONFIGURACIÓN BÁSICA ---
LOGIN_URL = "https://tusitio.com/login"      # Cambia esto por la URL real
AGENDA_URL = "https://tusitio.com/agenda"    # Cambia esto por la URL real
CRED = {"username": "USUARIO", "password": "CONTRASEÑA"}  # Credenciales de ejemplo

# Horas válidas (ajusta según tu caso)
HORAS_VALIDAS = [
    "08:00", "09:00", "10:00", "11:00", "12:00",
    "13:00", "14:00", "15:00", "16:00", "17:00"
]

# --- FUNCIONES AUXILIARES ---
def normalizar_hora(texto):
    """Limpia y estandariza el formato de hora."""
    match = re.search(r"(\d{1,2}:\d{2})", texto)
    return match.group(1) if match else None

def es_hora_valida(hora):
    """Verifica si la hora está dentro del rango permitido."""
    return hora in HORAS_VALIDAS

# --- FUNCIÓN PRINCIPAL ---
def obtener_disponibilidad():
    session = requests.Session()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # --- LOGIN ---
    try:
        response = session.post(LOGIN_URL, data=CRED, verify=False)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Error al iniciar sesión: {e}")

    # --- OBTENER AGENDA ---
    try:
        agenda_page = session.get(AGENDA_URL, verify=False)
        agenda_page.raise_for_status()
        soup = BeautifulSoup(agenda_page.text, 'html.parser')
    except Exception as e:
        raise Exception(f"Error al obtener la agenda: {e}")

    # --- PARSEAR DATOS ---
    disponibles_por_doctor = {}

    # Ajusta los selectores CSS según la estructura real del HTML
    for fila in soup.select("table.agenda tr"):
        columnas = fila.find_all("td")
        if len(columnas) >= 2:
            doctor = columnas[0].get_text(strip=True)
            hora = normalizar_hora(columnas[1].get_text(strip=True))
            if doctor and hora and es_hora_valida(hora):
                disponibles_por_doctor.setdefault(doctor, []).append(hora)

    return disponibles_por_doctor


# --- ENDPOINT PRINCIPAL ---
@app.route('/', methods=['GET'])
def home():
    """Endpoint raíz para confirmar que la API está activa."""
    return jsonify({
        "message": "✅ API Flask activa. Usa /api/disponibilidad para ver la disponibilidad."
    }), 200


# --- ENDPOINT API ---
@app.route('/api/disponibilidad', methods=['GET'])
def disponibilidad_endpoint():
    """Endpoint que devuelve la disponibilidad de doctores."""
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
    # Render asigna dinámicamente el puerto en la variable PORT
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
