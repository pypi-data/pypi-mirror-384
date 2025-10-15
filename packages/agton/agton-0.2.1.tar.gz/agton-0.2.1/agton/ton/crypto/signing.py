import nacl.signing
import nacl.exceptions

def private_key_to_public_key(private_key: bytes) -> bytes:
    return nacl.signing.SigningKey(private_key).verify_key.encode()

def sign(data: bytes, private_key: bytes) -> bytes:
    signer = nacl.signing.SigningKey(private_key)
    signed = signer.sign(data)
    return signed.signature

def verify(data: bytes, signature: bytes, public_key: bytes) -> bool:
    verifier = nacl.signing.VerifyKey(public_key)
    try:
        verifier.verify(data, signature)
        return True
    except nacl.exceptions.BadSignatureError:
        return False
