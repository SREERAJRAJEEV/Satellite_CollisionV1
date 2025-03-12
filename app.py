from flask import Flask, render_template, request, jsonify
import os
import pickle
import numpy as np
import json
import requests  # Import the requests library
from generateTrajectory import generate_trajectory
from skyfield.api import load, wgs84

app = Flask(__name__)

# Load XGBoost model
model_path = os.path.join("models", "xgboost.pkl")
with open(model_path, "rb") as model_file:
    model = pickle.load(model_file)

# Load demo satellites from JSON
demo_satellites_path = os.path.join("data", "demo_satellites.json")
with open(demo_satellites_path, "r") as demo_file:
    demo_satellites = json.load(demo_file)

# Function to fetch TLE satellite names from Celestrak
def fetch_tle_satellite_names():
    url = "https://www.celestrak.com/NORAD/elements/tle-new.txt"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            lines = response.text.split("\n")
            satellites = [lines[i].strip() for i in range(0, len(lines), 3) if lines[i].strip()]
            print("Fetched TLE satellites:", satellites)  # Debugging
            return satellites
        else:
            print(f"Failed to fetch TLE data. Status code: {response.status_code}")  # Debugging
            return []
    except Exception as e:
        print(f"Error fetching TLE data: {e}")  # Debugging
        return []

# Combine demo and TLE satellite names
def get_all_satellite_names():
    tle_satellites = fetch_tle_satellite_names()
    demo_satellite_names = [demo["name"] for demo in demo_satellites]
    print("TLE satellites:", tle_satellites)  # Debugging
    print("Demo satellites:", demo_satellite_names)  # Debugging
    return tle_satellites + demo_satellite_names

# Feature extraction for demo satellites
def extract_demo_features(satellite1, satellite2):
    high_risk_values = {
        "time_to_tca": 50,
        "max_risk_estimate": -3,  # Log scale closer to 0 = high risk
        "max_risk_scaling": 0.9,
        "miss_distance": 100,  # Very low miss distance
        "relative_speed": 8.0,
        "relative_position_r": 5,
        "relative_position_t": 3,
        "relative_position_n": 2,
        "relative_velocity_r": 1.5,
        "relative_velocity_t": 2.5,
        "geocentric_latitude": 45.0,
        "azimuth": 120.0,
        "elevation": 35.0,
        "F10": 150,
        "F3M": 300
    }
    return list(high_risk_values.values())

# Feature extraction for real satellites using Skyfield
def extract_real_features(satellite1, satellite2):
    # Load TLE data for the selected satellites
    ts = load.timescale()
    satellites = load.tle("https://www.celestrak.com/NORAD/elements/tle-new.txt")
    sat1 = satellites[satellite1]
    sat2 = satellites[satellite2]

    # Compute relative positions and velocities
    t = ts.now()
    geocentric1 = sat1.at(t)
    geocentric2 = sat2.at(t)
    relative_position = geocentric2 - geocentric1
    relative_velocity = sat2.at(t).velocity.km_per_s - sat1.at(t).velocity.km_per_s

    # Observer's position (example: latitude, longitude, elevation)
    observer_lat = 37.7749  # Latitude of San Francisco
    observer_lon = -122.4194  # Longitude of San Francisco
    observer_elevation = 0.0  # Elevation in meters
    observer = wgs84.latlon(observer_lat, observer_lon, observer_elevation)

    # Compute altitude and azimuth for satellite1
    altaz1 = (sat1 - observer).at(t).altaz()
    azimuth1 = altaz1[0].degrees  # Azimuth in degrees
    elevation1 = altaz1[1].degrees  # Elevation in degrees

    # Extract features
    features = {
        "time_to_tca": np.random.uniform(1, 100),  # Placeholder for TCA calculation
        "max_risk_estimate": np.random.uniform(-10, 0),
        "max_risk_scaling": np.random.uniform(0, 1),
        "miss_distance": relative_position.distance().km,
        "relative_speed": np.linalg.norm(relative_velocity),
        "relative_position_r": relative_position.position.km[0],
        "relative_position_t": relative_position.position.km[1],
        "relative_position_n": relative_position.position.km[2],
        "relative_velocity_r": relative_velocity[0],
        "relative_velocity_t": relative_velocity[1],
        "geocentric_latitude": geocentric1.subpoint().latitude.degrees,
        "azimuth": azimuth1,
        "elevation": elevation1,
        "F10": 150.0,  # Constant value
        "F3M": 3.5,  # Constant value
    }
    return list(features.values())

def extract_features(satellite1, satellite2):
    # Check if either satellite is a demo satellite
    if any(demo["name"] in [satellite1, satellite2] for demo in demo_satellites):
        return extract_demo_features(satellite1, satellite2)
    else:
        return extract_real_features(satellite1, satellite2)

def log_risk_to_percentage(log_risk):
    return (10 ** log_risk) * 100

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/generate_trajectory", methods=["POST"])
def generate():
    data = request.get_json()
    satellite_name = data.get("satellite")

    if not satellite_name:
        return jsonify({"error": "Satellite name is required"}), 400

    image_path = generate_trajectory(satellite_name)

    if image_path:
        return jsonify({"image": f"/{image_path}"})
    else:
        return jsonify({"error": "Satellite not found"}), 404

@app.route("/predict_risk", methods=["POST"])
def predict_risk():
    data = request.get_json()
    satellite1 = data.get("satellite1")
    satellite2 = data.get("satellite2")

    if not satellite1 or not satellite2:
        return jsonify({"error": "Both satellites must be selected"}), 400

    print(f"Predicting risk for satellites: {satellite1}, {satellite2}")  # Debugging

    try:
        features = extract_features(satellite1, satellite2)
        print(f"Extracted features: {features}")  # Debugging

        log_risk_value = model.predict([features])[0]  # Predict log risk
        risk_percentage = log_risk_to_percentage(log_risk_value)  # Convert to percentage
        risk_percentage_rounded = round(risk_percentage*100, 6)  # Round to 6 decimal places

        print(f"Predicted risk: {risk_percentage_rounded}%")  # Debugging

        return jsonify({"risk": risk_percentage_rounded})  # Send risk percentage
    except Exception as e:
        print(f"Error in /predict_risk: {e}")  # Debugging
        return jsonify({"error": str(e)}), 500

@app.route("/get_satellites", methods=["GET"])
def get_satellites():
    all_satellites = get_all_satellite_names()
    return jsonify({"satellites": all_satellites})

if __name__ == "__main__":
    app.run(debug=True)