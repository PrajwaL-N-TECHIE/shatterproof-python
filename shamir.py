import random
import binascii

# Mersenne Prime (2^127 - 1)
PRIME = 2**127 - 1

def _eval_at(poly, x, prime):
    """Evaluates polynomial (coefficient tuple) at x."""
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % prime
    return accum

def make_random_shares(secret, minimum, shares, prime=PRIME):
    """Generates random shares."""
    if minimum > shares:
        raise ValueError("Pool secret would be irrecoverable.")
    if minimum < 2:
        raise ValueError("Threshold must be at least 2")
    
    poly = [secret] + [random.randrange(prime) for i in range(minimum - 1)]
    points = []
    for i in range(1, shares + 1):
        x = i
        y = _eval_at(poly, x, prime)
        points.append((x, y))
    return points

def _extended_gcd(a, b):
    """Extended Euclidean Algorithm."""
    x, lastx = 0, 1
    y, lasty = 1, 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, lastx = lastx - quot * x, x
        y, lasty = lasty - quot * y, y
    return lastx, lasty

def _divmod(num, den, p):
    """Compute num / den modulo p."""
    inv, _ = _extended_gcd(den, p)
    return num * inv

def recover_secret(shares, prime=PRIME):
    """Recover the secret from share points (x, y) using Lagrange interpolation."""
    if len(shares) < 2:
        raise ValueError("need at least two shares")
    x_s, y_s = zip(*shares)
    num = 0
    for i in range(len(shares)):
        others = list(x_s)
        cur = others.pop(i)
        numerator = 1
        denominator = 1
        for o in others:
            numerator = (numerator * (-o)) % prime
            denominator = (denominator * (cur - o)) % prime
        value = y_s[i]
        lagrange_poly = (value * numerator * _divmod(1, denominator, prime)) % prime
        num = (num + lagrange_poly) % prime
    return num

# --- ROBUST TEXT WRAPPERS ---

def encrypt(text, total_shares=5, threshold=3):
    if not text:
        raise ValueError("Text cannot be empty")
    if threshold > total_shares:
        raise ValueError("Threshold cannot exceed total shares")
    if threshold < 2:
        raise ValueError("Threshold must be at least 2")
    
    try:
        # Convert string to hex bytes
        hex_data = binascii.hexlify(text.encode('utf-8'))
        # Convert hex bytes to integer
        secret_int = int(hex_data, 16)
        
        # Generate shares (x, y points)
        shares = make_random_shares(secret_int, threshold, total_shares)
        
        # Return as formatted strings
        return [f"{x}-{y}" for x, y in shares]
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")

def decrypt(share_strings):
    if not share_strings:
        raise ValueError("No shares provided")
    if len(share_strings) < 2:
        raise ValueError("Need at least 2 shares to reconstruct")
        
    shares = []
    for s in share_strings:
        if s and "-" in s:
            try:
                x, y = s.split("-")
                shares.append((int(x), int(y)))
            except ValueError:
                continue # Skip bad shards
            
    if len(shares) < 2:
        raise ValueError(f"Need at least 2 valid shares, got {len(shares)}")

    try:
        # Recover the big integer
        secret_int = recover_secret(shares)
        
        # Convert integer back to hex string
        hex_data = format(secret_int, 'x')
        
        # FIX: Ensure hex string has even length (e.g., 'f' -> '0f')
        if len(hex_data) % 2 != 0:
            hex_data = '0' + hex_data
            
        # Convert hex back to utf-8 string
        return binascii.unhexlify(hex_data).decode('utf-8')
    except Exception as e:
        # This usually happens if wrong shards are combined
        raise ValueError("Decryption failed. Shards mismatch or corrupted data.")

def validate_shard_format(shard_str):
    """Check if a shard string is properly formatted"""
    if not shard_str or '-' not in shard_str:
        return False
    try:
        x, y = shard_str.split('-')
        int(x)
        int(y)
        return True
    except ValueError:
        return False