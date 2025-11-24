import random
import binascii

# Mersenne Prime (2^127 - 1)
PRIME = 2**127 - 1

def _eval_at(poly, x, prime):
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % prime
    return accum

def make_random_shares(secret, minimum, shares, prime=PRIME):
    if minimum > shares:
        raise ValueError("Pool secret would be irrecoverable.")
    poly = [secret] + [random.randrange(prime) for i in range(minimum - 1)]
    points = []
    for i in range(1, shares + 1):
        x = i
        y = _eval_at(poly, x, prime)
        points.append((x, y))
    return points

def _extended_gcd(a, b):
    x, lastx = 0, 1
    y, lasty = 1, 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, lastx = lastx - quot * x, x
        y, lasty = lasty - quot * y, y
    return lastx, lasty

def _divmod(num, den, p):
    inv, _ = _extended_gcd(den, p)
    return num * inv

def recover_secret(shares, prime=PRIME):
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
    # Convert string to hex bytes
    hex_data = binascii.hexlify(text.encode('utf-8'))
    # Convert hex bytes to integer
    secret_int = int(hex_data, 16)
    
    # Generate shares (x, y points)
    shares = make_random_shares(secret_int, threshold, total_shares)
    
    # Return as formatted strings
    return [f"{x}-{y}" for x, y in shares]

def decrypt(share_strings):
    shares = []
    for s in share_strings:
        if "-" in s:
            try:
                x, y = s.split("-")
                shares.append((int(x), int(y)))
            except ValueError:
                continue # Skip bad shards
            
    if not shares:
        raise ValueError("No valid shards found")

    # Recover the big integer
    secret_int = recover_secret(shares)
    
    # Convert integer back to hex string
    hex_data = format(secret_int, 'x')
    
    # FIX: Ensure hex string has even length (e.g., 'f' -> '0f')
    # This was the bug causing garbled text!
    if len(hex_data) % 2 != 0:
        hex_data = '0' + hex_data
        
    try:
        # Convert hex back to utf-8 string
        return binascii.unhexlify(hex_data).decode('utf-8')
    except:
        return "[DECRYPTION ERROR: Bad Data]"