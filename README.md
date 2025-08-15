# Weather App by Hithashree M

A modern Flask-based web application that provides real-time weather data for any location worldwide. The app integrates the OpenWeatherMap API for weather information and the YouTube Data API to display related videos. It features local data persistence, CRUD operations, and multiple data export options.

## Features

- Search current weather by city or location with temperature, description, and icon.
- View relevant YouTube videos for the searched location.
- Store and manage weather data locally using a RESTful API and SQLite.
- Export weather data as JSON, CSV, PDF, or Markdown.
- Responsive UI with floating header, animations, and classic Times New Roman font for a clean look.

## Technologies Used

- Backend: Python, Flask, Flask-RESTful, SQLite3
- APIs: OpenWeatherMap, YouTube Data API
- Frontend: HTML5, CSS3, Jinja2 templating
- Libraries: Pandas, FPDF, dotenv

## Setup and Run

1. Clone the repository: https://github.com/HITHA-cpu/Weather_app.git
2. Install dependencies: pip install -r requirements.txt
3. Create a `.env` file with your API keys: WEATHER_API_KEY=your_openweathermap_api_key
                                            YOUTUBE_API_KEY=your_youtube_api_key
4. Run the app: python app.py
5. Open your browser and navigate to `http://127.0.0.1:5000/`

## License

This project is licensed under the MIT License.




