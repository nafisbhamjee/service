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
    service_name = data['name']  # Extract service name

    # Fetch existing services from JSONBin
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    services = response.json().get("record", {}).get("services", {})

    # Correctly save the service using its name as the key
    services[service_name] = {"ip": data['ip'], "port": data['port']}

    # Save the updated services list back to JSONBin
    update_response = requests.put(JSONBIN_URL, json={"services": services}, headers=HEADERS)

    if update_response.status_code == 200:
        return jsonify({"message": f"Service {service_name} registered correctly!"}), 200
    else:
        return jsonify({"error": "Failed to update service registry"}), 500


@app.route('/discover/<service_name>', methods=['GET'])
def discover(service_name):
    response = requests.get(JSONBIN_URL, headers=HEADERS)

    # Debug: Print the raw JSONBin response
    print("DEBUG: JSONBin Response:", response.json())

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch services"}), 500

    data = response.json()

    # Extract services correctly
    services = data.get("record", {}).get("services", {})

    if service_name in services:
        return jsonify(services[service_name]), 200
    return jsonify({"error": "Service not found"}), 404

@app.route('/discover/all', methods=['GET'])
def discover_all():
    response = requests.get(JSONBIN_URL, headers=HEADERS)
    return response.json()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
