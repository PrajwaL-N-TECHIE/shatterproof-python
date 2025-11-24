import random
import binascii

# A large prime number (Mersenne prime) to define the Finite Field
PRIME = 2**127 - 1

def _eval_at(poly, x, prime):
    """Evaluates polynomial (coefficient tuple) at x."""
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % prime
    return accum

def make_random_shares(secret, minimum, shares, prime=PRIME):
    """
    Generates a random polynomial with the secret as the constant term.
    Returns a list of tuples (x, y) representing the shares.
    """
    if minimum > shares:
        raise ValueError("Pool secret would be irrecoverable.")
    
    # Generate random coefficients
    poly = [secret] + [random.randrange(prime) for i in range(minimum - 1)]
    
    # Generate points (shares)
    points = []
    for i in range(1, shares + 1):
        x = i
        y = _eval_at(poly, x, prime)
        points.append((x, y))
    return points

def _extended_gcd(a, b):
    """Used for division in finite fields."""
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
    """
    Recover the secret from share points (x, y) using Lagrange interpolation.
    """
    if len(shares) < 2:
        raise ValueError("need at least two shares")
    
    x_s, y_s = zip(*shares)
    
    # Calculate the Lagrange basis polynomials at x=0
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

# --- Wrapper Functions for Text ---

def encrypt(text, total_shares=5, threshold=3):
    # 1. Text to Hex to Integer
    hex_data = binascii.hexlify(text.encode('utf-8'))
    secret_int = int(hex_data, 16)
    
    # 2. Generate Shares
    shares = make_random_shares(secret_int, threshold, total_shares)
    
    # 3. Format shares as strings "1-239482..."
    return [f"{x}-{y}" for x, y in shares]

def decrypt(share_strings):
    # 1. Parse strings "1-239482" back to tuples (1, 239482)
    shares = []
    for s in share_strings:
        if "-" in s:
            x, y = s.split("-")
            shares.append((int(x), int(y)))
            
    # 2. Math Recovery
    secret_int = recover_secret(shares)
    
    # 3. Integer to Hex to Text
    hex_data = format(secret_int, 'x')
    # Ensure even length for decoding
    if len(hex_data) % 2 != 0:
        hex_data = '0' + hex_data
        
    return binascii.unhexlify(hex_data).decode('utf-8')