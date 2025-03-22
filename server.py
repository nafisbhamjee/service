from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Using JSONBin.io as a free database
JSONBIN_URL = "https://api.jsonbin.io/v3/b/67df09398960c979a5767fed"
HEADERS = {"X-Master-Key": "$2a$10$4j8yKgEgSsJS0KyHF0qcyO1cGcUDvkTCqVCRj6D4Im1FpRuHdD5di"}

@app.route('/')
def home():
    return jsonify({"message": "Service Discovery is running!"})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    requests.put(JSONBIN_URL, json={"services": data}, headers=HEADERS)
    return jsonify({"message": f"Service {data['name']} registered!"}), 200

@app.route('/discover/<service_name>', methods=['GET'])
def discover(service_name):
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    services = response.json().get("record", {}).get("services", {})
    if service_name in services:
        return jsonify(services[service_name]), 200
    return jsonify({"error": "Service not found"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
