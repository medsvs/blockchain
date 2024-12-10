# quantum_proof.py

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64

# Function to simulate attack
def simulate_attacks():
    # Example of forged signature attack
    forged_signature_attack_result = forged_signature_attack()
    return forged_signature_attack_result

# Function to simulate forged signature attack
def forged_signature_attack():
    valid_voter_public_key = "valid_voter_public_key"  # Use real public key for validation
    attacker_forged_signature = "fake_forged_signature"  # Fake forged signature
    voter_id = "5000"  # Example voter ID

    # Verify the forged signature using RSA
    is_valid = verify_signature(valid_voter_public_key, voter_id, attacker_forged_signature)

    if is_valid:
        return "RSA Attack Failed: Forged signature accepted."
    else:
        return "RSA Attack Succeeded: Forged signature rejected."

def verify_signature(public_key, voter_id, forged_signature):
    try:
        # Public key should be real, here it's simulated
        key = RSA.import_key(public_key)
        h = SHA256.new(voter_id.encode())
        signature = base64.b64decode(forged_signature)
        pkcs1_15.new(key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False
