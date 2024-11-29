from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "HTTP Server running on Flask"

@app.route('/receive_dni', methods=['POST'])
def receive_dni():
    try:
        data = request.get_json()
        dni_confirmed = data.get('dni_confirmed')
        if not dni_confirmed:
            return jsonify({"status": "error", "message": "DNI not provided"}), 400

        # Print and log the received data
        print(f"DNI confirmado recibido: {dni_confirmed}")
        with open("received_data.log", "a") as log_file:
            log_file.write(f"Received DNI: {dni_confirmed}\n")

        return jsonify({"status": "success", "message": "DNI received successfully"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": f"Error processing request: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)