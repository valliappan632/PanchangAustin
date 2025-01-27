from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
CORS(app)  # Enable CORS to handle cross-origin requests

def get_sunrise_sunset(lat, lng, date='today'):
    """
    Fetches sunrise and sunset times for the given latitude and longitude.
    """
    url = "https://api.sunrise-sunset.org/json"
    params = {
        'lat': lat,
        'lng': lng,
        'date': date,
        'formatted': 0  # Use UTC (unformatted) times
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', {})
    else:
        return {'error': f"Failed to fetch data. HTTP Status Code: {response.status_code}"}

def convert_to_local_time(utc_time_str, timezone_str):
    """
    Converts UTC time string to local timezone.
    """
    utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
    local_tz = pytz.timezone(timezone_str)
    local_time = utc_time.astimezone(local_tz)
    return local_time

def calculate_periods(sunrise, sunset, timezone_str):
    """
    Calculate Rahu Kalam, Yamagandam, and Gulikai Kalam for a given sunrise and sunset.
    """
    daylight_duration = sunset - sunrise
    segment_duration = daylight_duration / 8

    # Periods for Monday
    rahu_start = sunrise + segment_duration  # 2nd segment starts
    rahu_end = rahu_start + segment_duration

    yam_start = sunrise + 3 * segment_duration  # 4th segment starts
    yam_end = yam_start + segment_duration

    gulikai_start = sunrise + 5 * segment_duration  # 6th segment starts
    gulikai_end = gulikai_start + segment_duration

    # Convert to local timezone
    local_tz = pytz.timezone(timezone_str)
    return {
        "Rahu Kalam": f"{rahu_start.astimezone(local_tz).strftime('%I:%M %p')} to {rahu_end.astimezone(local_tz).strftime('%I:%M %p')}",
        "Yamagandam": f"{yam_start.astimezone(local_tz).strftime('%I:%M %p')} to {yam_end.astimezone(local_tz).strftime('%I:%M %p')}",
        "Gulikai Kalam": f"{gulikai_start.astimezone(local_tz).strftime('%I:%M %p')} to {gulikai_end.astimezone(local_tz).strftime('%I:%M %p')}",
    }

@app.route('/')
def index():
    """
    Serve the index.html file.
    """
    return render_template('index.html')

@app.route('/sunrise-sunset', methods=['GET'])
def sunrise_sunset():
    """
    API endpoint to get sunrise, sunset, Rahu Kalam, Yamagandam, and Gulikai timings.
    """
    # Default latitude and longitude for Austin, Texas
    lat = request.args.get('lat', default=30.2672, type=float)  # Austin Latitude
    lng = request.args.get('lng', default=-97.7431, type=float)  # Austin Longitude
    date = request.args.get('date', default='today', type=str)  # Default is today

    sun_times = get_sunrise_sunset(lat, lng, date)
    if 'error' in sun_times:
        return jsonify({'error': sun_times['error']}), 400

    timezone = 'America/Chicago'  # Central Standard Time (CST)
    sunrise_utc = convert_to_local_time(sun_times['sunrise'], timezone)
    sunset_utc = convert_to_local_time(sun_times['sunset'], timezone)

    periods = calculate_periods(sunrise_utc, sunset_utc, timezone)

    return jsonify({
        'Sunrise': sunrise_utc.strftime("%I:%M %p"),
        'Sunset': sunset_utc.strftime("%I:%M %p"),
        'Rahu Kalam': periods['Rahu Kalam'],
        'Yamagandam': periods['Yamagandam'],
        'Gulikai Kalam': periods['Gulikai Kalam']
    })

if __name__ == '__main__':
    app.run(debug=True)
