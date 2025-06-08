import base64
import binascii
import hashlib
import hmac


def createSignature(clientId, publicKey, privateKey, nonce):
    # Remove 'b ' prefix if present
    clientId = clientId.replace("b ", "") if clientId.startswith("b ") else clientId
    publicKey = publicKey.replace("b ", "") if publicKey.startswith("b ") else publicKey
    privateKey = (
        privateKey.replace("b ", "") if privateKey.startswith("b ") else privateKey
    )

    # Try base64 decoding the private key
    try:
        private_key_bytes = base64.b64decode(privateKey)
    except (ValueError, binascii.Error):
        private_key_bytes = privateKey.encode("utf-8")

    message = f"{nonce}{clientId}{publicKey}"
    signature = hmac.new(
        private_key_bytes, message.encode("utf-8"), digestmod=hashlib.sha256
    ).hexdigest()
    return signature.upper()
