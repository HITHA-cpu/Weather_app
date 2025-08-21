import os
import sqlite3
import requests
from flask import Flask, request, render_template, jsonify, Response
from flask_restful import Api, Resource
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from fpdf import FPDF

# Load environment variables
load_dotenv()

# Flask app and API initialization
app = Flask(__name__)
api = Api(app)

# API keys from environment
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Database name
DB_NAME = 'weather.db'

# Database initialization
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                date TEXT NOT NULL,
                weather_info TEXT NOT NULL
            )
        ''')
init_db()

# --- ROUTES ---

# Home Route
@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None
    error = None
    if request.method == 'POST':
        location = request.form.get('location')
        if not location:
            error = "Please enter a location!"
        else:
            try:
                weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
                res = requests.get(weather_url)
                data = res.json()
                if data.get('cod') != 200:
                    error = data.get('message', 'Error fetching weather')
                else:
                    weather = {
                        'location': f"{data['name']}, {data['sys']['country']}",
                        'temperature': data['main']['temp'],
                        'description': data['weather'][0]['description'],
                        'icon': data['weather'][0]['icon']
                    }
            except Exception as e:
                error = f"Error: {str(e)}"

    return render_template('index.html', weather=weather, error=error)

# Info Page
@app.route('/info')
def info():
    return render_template('info.html')

# YouTube Videos Route
@app.route('/youtube_videos', methods=['GET'])
def youtube_videos():
    location = request.args.get('location')
    if not location:
        return "Location not specified", 400

    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': location,
        'key': YOUTUBE_API_KEY,
        'maxResults': 5,
        'type': 'video'
    }
    response = requests.get(search_url, params=params)
    results = response.json().get('items', [])

    videos = []
    for item in results:
        videos.append({
            'title': item['snippet']['title'],
            'thumbnail': item['snippet']['thumbnails']['medium']['url'],
            'video_id': item['id']['videoId']
        })

    return render_template('youtube_videos.html', videos=videos, location=location)

# --- CRUD API CLASS ---
class WeatherData(Resource):

    def get(self, record_id=None):
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if record_id:
                cur.execute("SELECT * FROM weather_data WHERE id=?", (record_id,))
                row = cur.fetchone()
                if row:
                    return dict(row), 200
                return {"message": "Record not found"}, 404
            cur.execute("SELECT * FROM weather_data")
            rows = cur.fetchall()
            return [dict(row) for row in rows], 200

    def post(self):
        data = request.get_json()
        location = data.get('location')
        date = data.get('date')
        weather_info = data.get('weather_info')

        try:
            datetime.strptime(date, '%Y-%m-%d')
        except:
            return {"message": "Invalid date format, should be YYYY-MM-DD"}, 400

        if not location or not weather_info:
            return {"message": "Missing required fields"}, 400

        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO weather_data (location, date, weather_info) VALUES (?, ?, ?)",
                        (location, date, weather_info))
            conn.commit()
            return {"message": "Record created", "id": cur.lastrowid}, 201

    def put(self, record_id):
        data = request.get_json()
        weather_info = data.get('weather_info')

        if not weather_info:
            return {"message": "Missing weather_info for update"}, 400

        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM weather_data WHERE id=?", (record_id,))
            if not cur.fetchone():
                return {"message": "Record not found"}, 404
            cur.execute("UPDATE weather_data SET weather_info=? WHERE id=?", (weather_info, record_id))
            conn.commit()
            return {"message": "Record updated"}, 200

    def delete(self, record_id):
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM weather_data WHERE id=?", (record_id,))
            if not cur.fetchone():
                return {"message": "Record not found"}, 404
            cur.execute("DELETE FROM weather_data WHERE id=?", (record_id,))
            conn.commit()
            return {"message": "Record deleted"}, 200

# Register CRUD resource
api.add_resource(WeatherData, '/api/weather', '/api/weather/<int:record_id>')

# --- EXPORT ROUTES ---

# Export JSON or CSV
@app.route('/export')
def export():
    fmt = request.args.get('format', 'json').lower()
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM weather_data", conn)

    if fmt == 'csv':
        csv_data = df.to_csv(index=False)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=weather_data.csv"}
        )
    else:
        return df.to_json(orient='records')

# Export as PDF
@app.route('/export/pdf')
def export_pdf():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT location, date, weather_info FROM weather_data")
        rows = cur.fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Weather Data Export", ln=True, align='C')

    for loc, date, weather in rows:
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"{loc} - {date}", ln=True)
        pdf.multi_cell(0, 10, txt=weather)

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return Response(pdf_output, mimetype='application/pdf', headers={"Content-Disposition": "attachment;filename=weather_data.pdf"})

# Export as Markdown
@app.route('/export/markdown')
def export_markdown():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT location, date, weather_info FROM weather_data")
        rows = cur.fetchall()

    md_content = "# Weather Data Export\n\n"
    for loc, date, weather in rows:
        md_content += f"## {loc} - {date}\n\n{weather}\n\n"

    return Response(md_content, mimetype='text/markdown', headers={"Content-Disposition": "attachment;filename=weather_data.md"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Render!"

