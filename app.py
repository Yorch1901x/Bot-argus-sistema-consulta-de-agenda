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

# Horas válidas (ajusta según tus reglas)
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
    return hora in HORAS_VALIDAS

# --- FUNCIÓN PRINCIPAL (por ahora modo MOCK) ---
def obtener_disponibilidad():
    """
    Modo mock (datos simulados). 
    Puedes reemplazar esto más adelante por el scraping real.
    """
    disponibles_por_doctor = {
        "Dr. Pérez": ["09:00", "10:00", "11:00"],
        "Dra. Gómez": ["14:00", "15:00"],
        "Dr. Ramírez": ["08:00", "13:00", "16:00"]
    }
    return disponibles_por_doctor

# --- ENDPOINT PRINCIPAL (para ver si la API está viva) ---
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "✅ API Flask activa. Usa /api/disponibilidad para ver los datos de ejemplo."
    }), 200

# --- ENDPOINT API DISPONIBILIDAD ---
@app.route('/api/disponibilidad', methods=['GET'])
def disponibilidad_endpoint():
    try:
        data = obtener_disponibilidad()
        return jsonify({
            "status": "success",
            "data": data,
            "message": "Disponibilidad obtenida correctamente (modo mock)."
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
