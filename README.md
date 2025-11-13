🩺 Argus Medical Availability Scraper API
Real-time doctor availability extraction via automated scraping

This project is a Python + Flask API that retrieves real-time medical appointment availability from the Grupo Argus scheduling system using automated scraping.

It is designed for:

Virtual assistants (VAPI, DialogFlow, Rasa, etc.)

Medical scheduling systems

Workflow automation

WhatsApp or web-based appointment bots

Clinics that need direct access to internal scheduling

🚀 Key Features

✔ Automatic login to the Argus scheduling platform
✔ Fetch availability for a specific date
✔ Fetch availability for a specific doctor
✔ Real-time extraction of available appointment slots (30-minute blocks)
✔ Clean, bot-friendly JSON responses
✔ Automated handling of ASP.NET __VIEWSTATE and __EVENTVALIDATION fields
✔ Persistent session handling with cookies
✔ API ready for integration with smart appointment systems

🧠 How It Works

The scraper performs the following:

Automatically logs into the Grupo Argus scheduling system.

Loads the agenda for the selected date.

Parses the HTML table containing doctors and time slots.

Detects available vs occupied blocks.

Returns a clean JSON structure compatible with bots and backends.

The user does not see any of this — it runs fully in the background.

🔧 Technologies Used

Python 3

Flask

Requests

BeautifulSoup4

Gunicorn (for deployment on services like Render.com)

📦 Installation

Clone the repository:

git clone https://github.com/your-username/argus-medical-scraper.git
cd argus-medical-scraper


Install dependencies:

pip install -r requirements.txt

▶️ Run the Server
python app.py


The API will be available at:

http://localhost:5000

📡 API Endpoints
📍 1. Get availability for all doctors
GET /api/disponibilidad?fecha=YYYY-MM-DD


Example:

/api/disponibilidad?fecha=2025-11-15


Response:

{
  "status": "success",
  "data": {
    "fecha": "15/11/2025",
    "disponibilidad": {
      "Dr. Rodríguez": [
        { "hora": "8:30 a. m.", "detalle": "Disponible" }
      ],
      "Dr. López": []
    }
  }
}

📍 2. Get availability for a specific doctor
GET /api/disponibilidad/Doctor_Name?fecha=YYYY-MM-DD


Example:

/api/disponibilidad/Daniela_Rivera?fecha=2025-11-15


Response:

{
  "status": "success",
  "doctor": "Daniela Rivera",
  "fecha": "15/11/2025",
  "disponibilidad": [
    { "hora": "9:00 a. m.", "detalle": "Disponible" }
  ]
}

🔒 Error Handling

The API provides clear and structured error messages for:

Invalid date format

Login failures

Missing or malformed agenda tables

No doctors detected

Doctor not found

Unexpected website structure changes

Example:

{
  "status": "error",
  "message": "Doctor not found in the schedule"
}

🏥 Recommended for Virtual Assistant Integrations

Perfect for bots that must:

Validate availability before offering times

Suggest only valid appointment slots

Integrate with Google Calendar or other schedulers

Prevent double-booking

Example usage from VAPI:

GET https://argus-scraper-api.onrender.com/api/disponibilidad/Daniela_Rivera?fecha=2025-11-15

🗂 Project Structure
├── app.py                 # Scraping logic + Flask API
├── Procfile               # Deployment configuration
├── requirements.txt       # Python dependencies
├── README.md              # Documentation

🌐 Deployment

This API deploys seamlessly on:

Render.com

Railway.app

Fly.io

VPS (Gunicorn + Nginx)

A complete Procfile is already included:

web: gunicorn app:app

🤝 Contributing

Contributions are welcome!
Feel free to open an issue, create a pull request, or fork the project.

📄 License

Choose any license you prefer (MIT is commonly used).
Add a LICENSE file if you want open-source distribution.

❤️ Author

Your Name or Organization
Medical appointment availability API for Clínica Luximed
Built with Python and automation passion 🩵

If you want, I can also generate:

✅ A highly visual README with banners and badges
✅ A version with diagrams (flowcharts or architecture)
✅ A downloadable .md file
Just let me know!
