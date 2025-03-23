from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# JSONBin API Setup
JSONBIN_URL = "https://api.jsonbin.io/v3/b/67df09398960c979a5767fed"
HEADERS = {"X-Master-Key": "$2a$10$4j8yKgEgSsJS0KyHF0qcyO1cGcUDvkTCqVCRj6D4Im1FpRuHdD5di"}

# ==============================
# 🚀 1️⃣ REGISTER A SERVICE
# ==============================
@app.route('/register', methods=['POST'])
def register_service():
    """Registers a microservice only if it is actually running"""
    try:
        data = request.json
        service_name = data.get("name")
        ip = data.get("ip")
        port = data.get("port")

        # ✅ Try multiple connection methods (Localhost, Internal IP, External IP)
        possible_urls = [
            f"http://{ip}:{port}/health",  
            f"http://127.0.0.1:{port}/health"  # Try localhost for local registrations
        ]

        # ✅ Attempt all possible URLs
        health_check_success = False
        for health_url in possible_urls:
            try:
                health_response = requests.get(health_url, timeout=3)
                if health_response.status_code == 200:
                    health_check_success = True
                    break  # Stop checking if any URL works
            except requests.exceptions.RequestException:
                continue  # Try the next URL

        if not health_check_success:
            return jsonify({
                "error": f"Could not reach {service_name}. Registration failed."
            }), 400

        # ✅ Fetch the latest JSONBin data
        response = requests.get(JSONBIN_URL, headers=HEADERS)
        if response.status_code != 200:
            return jsonify({
                "error": f"Failed to fetch services. JSONBin Status: {response.status_code}",
                "details": response.text
            }), 500

        json_data = response.json().get("record", {})

        # ✅ Ensure "services" and "messages" keys exist
        existing_services = json_data.get("services", {})
        existing_messages = json_data.get("messages", {})

        # ✅ Register the service
        existing_services[service_name] = {
            "ip": ip,
            "port": port,
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }

        # ✅ Save the update back to JSONBin
        put_response = requests.put(JSONBIN_URL, json={
            "services": existing_services, 
            "messages": existing_messages  # Preserve messages!
        }, headers=HEADERS)

        if put_response.status_code != 200:
            return jsonify({
                "error": f"Failed to update JSONBin. Status: {put_response.status_code}",
                "details": put_response.text
            }), 500

        return jsonify({"status": f"Service '{service_name}' registered!"}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "JSONBin request failed",
            "details": str(e)
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500

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
    """Microservices push messages to the relay while preserving services"""
    try:
        data = request.json
        sender = data.get("sender")
        recipient = data.get("recipient")
        message = data.get("message")

        response = requests.get(JSONBIN_URL, headers=HEADERS)

        # 🚨 Handle JSONBin Failure
        if response.status_code != 200:
            return jsonify({
                "error": f"Failed to fetch messages. JSONBin Status: {response.status_code}",
                "details": response.text
            }), 500

        json_data = response.json().get("record", {})

        # ✅ Ensure "services" and "messages" keys exist
        json_data.setdefault("services", {})
        json_data.setdefault("messages", {})

        if recipient not in json_data["messages"]:
            json_data["messages"][recipient] = []

        json_data["messages"][recipient].append({
            "from": sender,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # ✅ Update JSONBin while keeping both keys
        put_response = requests.put(JSONBIN_URL, json=json_data, headers=HEADERS)

        if put_response.status_code != 200:
            return jsonify({
                "error": f"Failed to update JSONBin. Status: {put_response.status_code}",
                "details": put_response.text
            }), 500

        return jsonify({"status": "Message stored"}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "JSONBin request failed",
            "details": str(e)
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500

# ==============================
# 🚀 4️⃣ GET MESSAGES FOR A MICROSERVICE
# ==============================
@app.route('/relay/receive/<recipient>', methods=['GET'])
def get_messages(recipient):
    """Microservices pull messages from the relay"""
    try:
        response = requests.get(JSONBIN_URL, headers=HEADERS)
        
        # 🚨 Handle JSONBin Failure
        if response.status_code != 200:
            return jsonify({
                "error": f"Failed to fetch messages. JSONBin Status: {response.status_code}",
                "details": response.text
            }), 500

        json_data = response.json().get("record", {})

        # ✅ Ensure "messages" key exists
        if "messages" not in json_data:
            json_data["messages"] = {}

        messages = json_data["messages"].get(recipient, [])

        # Clear messages only if recipient exists
        json_data["messages"][recipient] = []

        requests.put(JSONBIN_URL, json={"messages": json_data["messages"]}, headers=HEADERS)

        return jsonify({"messages": messages})  # ✅ Always return JSON

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "JSONBin request failed",
            "details": str(e)
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500
    

# ==============================
# 🚀 5️⃣ LIST ALL REGISTERED SERVICES
# ==============================
@app.route('/services', methods=['GET'])
def list_services():
    """Returns a list of all registered services"""
    try:
        response = requests.get(JSONBIN_URL, headers=HEADERS)

        # 🚨 Check if JSONBin API call failed
        if response.status_code != 200:
            return jsonify({
                "error": f"Failed to fetch services. JSONBin Status: {response.status_code}",
                "details": response.text
            }), 500

        # 🚨 Handle potential JSON decoding errors
        try:
            json_data = response.json()
        except requests.exceptions.JSONDecodeError:
            return jsonify({
                "error": "Invalid JSON response from JSONBin",
                "details": response.text
            }), 500

        # ✅ Ensure "record" key exists
        json_data = json_data.get("record", {})

        # ✅ Ensure "services" exists, otherwise return an empty dict
        services = json_data.get("services", {})

        return jsonify({"services": services}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "JSONBin request failed",
            "details": str(e)
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
