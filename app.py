from flask import Flask, render_template, request, jsonify
import shamir
from datetime import datetime

app = Flask(__name__)

# Simple in-memory rate limiting (resets on server restart)
request_times = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shatter', methods=['POST'])
def shatter():
    # Basic Rate Limiting Logic
    client_ip = request.remote_addr
    now = datetime.now().timestamp()
    
    if client_ip in request_times:
        if now - request_times[client_ip] < 0.5:  # Limit: 2 requests per second
            return jsonify({"status": "error", "message": "Slow down! Rate limit exceeded."})
    
    request_times[client_ip] = now
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data"})

    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({"status": "error", "message": "No text provided"})
    
    if len(text) > 100000:  # 100KB limit
        return jsonify({"status": "error", "message": "Text too long (max 100KB)"})
    
    try:
        # Clamp values to safe limits
        total_shares = max(2, min(int(data.get('total_shares', 5)), 20))  # Max 20 shares
        threshold = max(2, min(int(data.get('threshold', 3)), total_shares))
        
        # Create shards
        shards = shamir.encrypt(text, total_shares=total_shares, threshold=threshold)
        return jsonify({
            "status": "success", 
            "shards": shards,
            "total_shares": total_shares,
            "threshold": threshold
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/reconstruct', methods=['POST'])
def reconstruct():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data"})

    shards = data.get('shards', [])
    
    # Filter out empty/invalid shards before passing to logic
    valid_shards = [s for s in shards if s and shamir.validate_shard_format(s)]
    
    if len(valid_shards) < 2:
        return jsonify({
            "status": "error", 
            "message": f"Need at least 2 valid shards, got {len(valid_shards)}"
        })
    
    try:
        secret = shamir.decrypt(valid_shards)
        return jsonify({"status": "success", "secret": secret})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)})
    except Exception as e:
        return jsonify({"status": "error", "message": "Decryption failed. Shards mismatch."})

@app.route('/validate_shards', methods=['POST'])
def validate_shards():
    """Check if provided shards are valid format"""
    data = request.json
    shards = data.get('shards', [])
    
    valid_count = sum(1 for s in shards if s and shamir.validate_shard_format(s))
    
    if valid_count > 0:
        return jsonify({
            "status": "success", 
            "valid": True,
            "shard_count": valid_count,
            "message": f"Found {valid_count} valid shard formats"
        })
    else:
        return jsonify({
            "status": "success",
            "valid": False,
            "shard_count": 0,
            "message": "No valid shards found"
        })

if __name__ == '__main__':
    app.run(debug=True)