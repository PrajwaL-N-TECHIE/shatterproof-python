from flask import Flask, render_template, request, jsonify
import shamir
from datetime import datetime

app = Flask(__name__)

# Rate limiting storage (in production, use Redis)
request_times = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shatter', methods=['POST'])
def shatter():
    # Basic rate limiting
    client_ip = request.remote_addr
    now = datetime.now().timestamp()
    
    if client_ip in request_times:
        if now - request_times[client_ip] < 1:  # 1 second between requests
            return jsonify({"status": "error", "message": "Rate limit exceeded"})
    
    request_times[client_ip] = now
    
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({"status": "error", "message": "No text provided"})
    
    if len(text) > 100000:  # 100KB limit
        return jsonify({"status": "error", "message": "Text too long (max 100KB)"})
    
    try:
        total_shares = min(int(data.get('total_shares', 5)), 10)  # Max 10 shares
        threshold = min(int(data.get('threshold', 3)), total_shares)
        
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
    shards = data.get('shards', [])
    
    # Filter out empty/invalid shards
    valid_shards = [s for s in shards if s and shamir.validate_shard_format(s)]
    
    if len(valid_shards) < 2:
        return jsonify({
            "status": "error", 
            "message": f"Need at least 2 valid shards, got {len(valid_shards)}"
        })
    
    try:
        secret = shamir.decrypt(valid_shards)
        return jsonify({"status": "success", "secret": secret})
    except Exception as e:
        return jsonify({"status": "error", "message": "Decryption failed. Shards mismatch."})

@app.route('/validate_shards', methods=['POST'])
def validate_shards():
    """Check if provided shards can reconstruct a secret"""
    data = request.json
    shards = data.get('shards', [])
    
    valid_shards = [s for s in shards if s and shamir.validate_shard_format(s)]
    
    try:
        secret = shamir.decrypt(valid_shards)
        return jsonify({
            "status": "success", 
            "valid": True,
            "shard_count": len(valid_shards),
            "message": f"Valid configuration: {len(valid_shards)} shards"
        })
    except:
        return jsonify({
            "status": "success",
            "valid": False,
            "shard_count": len(valid_shards),
            "message": f"Insufficient shards: {len(valid_shards)} provided"
        })

if __name__ == '__main__':
    print("🔥 ShatterProof System Online: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)