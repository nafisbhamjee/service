from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# JSONBin API Setup
JSONBIN_URL = "https://api.jsonbin.io/v3/b/67df09398960c979a5767fed"
HEADERS = {"X-Master-Key": "$2a$10$4j8yKgEgSsJS0KyHF0qcyO1cGcUDvkTCqVCRj6D4Im1FpRuHdD5di"}

# ==============================
# 🚀 1️⃣ REGISTER A SERVICE
# ==============================
@app.route('/register', methods=['POST'])
def register_service():
    """Registers a microservice with the relay"""
    data = request.json
    service_name = data.get("name")
    ip = data.get("ip")
    port = data.get("port")

    # Fetch current services
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    json_data = response.json().get("record", {})

    if "services" not in json_data:
        json_data["services"] = {}

    json_data["services"][service_name] = {
        "ip": ip,
        "port": port,
        "lastUpdated": datetime.utcnow().isoformat()
    }

    requests.put(JSONBIN_URL, json={"services": json_data["services"]}, headers=HEADERS)
    return jsonify({"status": f"Service '{service_name}' registered!"}), 200

# ==============================
# 🚀 2️⃣ DISCOVER A SERVICE
# ==============================
@app.route('/discover/<service_name>', methods=['GET'])
def discover_service(service_name):
    """Find a registered microservice"""
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    services = response.json().get("record", {}).get("services", {})

    if service_name in services:
        return jsonify(services[service_name]), 200
    return jsonify({"error": "Service not found"}), 404

# ==============================
# 🚀 3️⃣ STORE MESSAGE IN RELAY
# ==============================
@app.route('/relay/send', methods=['POST'])
def store_message():
    """Microservices push messages to the relay"""
    data = request.json
    sender = data.get("sender")
    recipient = data.get("recipient")
    message = data.get("message")

    # Fetch current messages
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    json_data = response.json().get("record", {})

    if "messages" not in json_data:
        json_data["messages"] = {}

    if recipient not in json_data["messages"]:
        json_data["messages"][recipient] = []

    json_data["messages"][recipient].append({
        "from": sender,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })

    requests.put(JSONBIN_URL, json={"messages": json_data["messages"]}, headers=HEADERS)
    return jsonify({"status": "Message stored"}), 200

# ==============================
# 🚀 4️⃣ GET MESSAGES FOR A MICROSERVICE
# ==============================
@app.route('/relay/receive/<recipient>', methods=['GET'])
def get_messages(recipient):
    """Microservices pull messages from the relay"""
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    json_data = response.json().get("record", {})

    messages = json_data.get("messages", {}).get(recipient, [])

    # Clear messages once fetched
    json_data["messages"][recipient] = []
    requests.put(JSONBIN_URL, json={"messages": json_data["messages"]}, headers=HEADERS)

    return jsonify({"messages": messages}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
