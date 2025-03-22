from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# JSONBin API Setup
JSONBIN_URL = "https://api.jsonbin.io/v3/b/YOUR_BIN_ID"
HEADERS = {"X-Master-Key": "YOUR_API_KEY"}

# Caching Services to Reduce API Calls
CACHE = {}
CACHE_TTL = 60  # 1 minute cache expiration

# ==============================
# 🚀 1️⃣ SERVICE DISCOVERY API
# ==============================

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    service_name = data['name']

    # Fetch existing services
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    services = response.json().get("record", {}).get("services", {})

    # Add or Update the Service (with timestamp for expiration)
    services[service_name] = {
        "ip": data["ip"],
        "port": data["port"],
        "lastUpdated": datetime.utcnow().isoformat()
    }

    # Save to JSONBin
    update_response = requests.put(JSONBIN_URL, json={"services": services}, headers=HEADERS)
    return jsonify({"message": f"Service {service_name} registered!"}), 200

@app.route('/discover/<service_name>', methods=['GET'])
def discover(service_name):
    now = datetime.utcnow()

    # Check cache first
    if service_name in CACHE:
        cached_service, cache_time = CACHE[service_name]
        if (now - cache_time).seconds < CACHE_TTL:
            return jsonify(cached_service), 200  # Return cached service

    # Fetch from JSONBin
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    services = response.json().get("record", {}).get("services", {})

    # Remove expired services
    expiration_time = timedelta(minutes=10)
    if service_name in services:
        service_data = services[service_name]
        last_updated = datetime.fromisoformat(service_data["lastUpdated"])
        
        if now - last_updated > expiration_time:
            del services[service_name]  # Remove expired service
            requests.put(JSONBIN_URL, json={"services": services}, headers=HEADERS)
            return jsonify({"error": "Service expired"}), 404

        # Store in cache
        CACHE[service_name] = (service_data, now)
        return jsonify(service_data), 200

    return jsonify({"error": "Service not found"}), 404

@app.route('/monitor', methods=['GET'])
def monitor_services():
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    return response.json()

# ==============================
# 🚀 2️⃣ CLOUD RELAY (Dynamic Routing)
# ==============================

@app.route('/proxy/<service_name>', methods=['POST', 'GET'])
def proxy(service_name):
    """Cloud Relay: Forward requests to any registered microservice"""
    response = requests.get(f"https://service-9ubg.onrender.com/discover/{service_name}")
    
    if response.status_code != 200:
        return jsonify({"error": f"Service '{service_name}' not found"}), 404

    service_data = response.json()
    target_url = f"http://{service_data['ip']}:{service_data['port']}{request.full_path.replace('/proxy', '')}"

    if request.method == "POST":
        response = requests.post(target_url, json=request.get_json())
    else:
        response = requests.get(target_url)

    return response.content, response.status_code

# ==============================
# 🚀 Run the App
# ==============================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
