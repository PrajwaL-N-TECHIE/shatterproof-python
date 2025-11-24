from flask import Flask, render_template, request, jsonify
import shamir

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shatter', methods=['POST'])
def shatter():
    data = request.json
    text = data.get('text', '')
    
    try:
        # Create 5 shards, require 3 to unlock
        shards = shamir.encrypt(text, total_shares=5, threshold=3)
        return jsonify({"status": "success", "shards": shards})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/reconstruct', methods=['POST'])
def reconstruct():
    data = request.json
    shards = data.get('shards', [])
    
    try:
        secret = shamir.decrypt(shards)
        return jsonify({"status": "success", "secret": secret})
    except Exception as e:
        # If decryption fails (wrong math), return error
        return jsonify({"status": "error", "message": "Decryption failed. Shards mismatch."})

if __name__ == '__main__':
    print("🔥 ShatterProof System Online: http://127.0.0.1:5000")
    app.run(debug=True)