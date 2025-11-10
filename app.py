# app.py (ejemplo de cómo se vería el inicio del script con Flask)
from bs4 import BeautifulSoup
import requests
import urllib3
import json
import re
from flask import Flask, jsonify # Importar Flask y jsonify

# ... (Mantén todas tus variables y funciones auxiliares: LOGIN_URL, AGENDA_URL, CRED, HORAS_VALIDAS, normalizar_hora, es_hora_valida) ...

app = Flask(__name__)

# Función principal que contiene toda la lógica de scraping
def obtener_disponibilidad():
    # --- LOGIN ---
    # ... (Tu lógica de login) ...
    
    # --- OBTENER TABLA DE AGENDA ---
    # ... (Tu lógica para obtener la tabla y doctores) ...

    # --- MAPA DE DISPONIBILIDAD (CORREGIDO) ---
    # ... (Tu lógica para iterar la tabla y obtener disponibles_por_doctor) ...

    # --- FILTRAR Y DEVOLVER ---
    # En lugar de imprimir y guardar el JSON, simplemente devuélvelo.
    disponibles_final = {
        doc: [d for d in lista if es_hora_valida(d.split(" - ")[0])]
        for doc, lista in disponibles_por_doctor.items()
    }
    
    # Opcional: Si quieres un resumen más limpio para el bot
    resumen_disponibilidad = {}
    for doc, espacios in disponibles_final.items():
        resumen_disponibilidad[doc] = [s.split(" - ")[0] for s in espacios]

    return resumen_disponibilidad

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
        # Esto es importante para el debugging en Render
        return jsonify({
            "status": "error",
            "message": f"Error al obtener disponibilidad: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Usar el puerto 10000 o el que Render asigne (se usará Gunicorn en producción)
    app.run(debug=True, port=8000)