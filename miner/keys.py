import ecdsa
import hashlib
import base58

class generate():
    def __init__(self):
        hashKey = hashlib.sha256(b'your-secret-seed').hexdigest()
        self.privateKey = ecdsa.SigningKey.from_string(bytes.fromhex(hashKey), curve=ecdsa.SECP256k1)
        self.publicKey = self.privateKey.get_verifying_key()

        self.stringPublicKey = base58.b58encode(self.publicKey.to_string()).decode('utf-8')

    def save(self):
        open('./keys/private.key', 'wb').write(self.privateKey.to_string())
        open('./keys/public.key', 'wb').write(self.publicKey.to_string())

    def load(self):
        self.privateKey = ecdsa.SigningKey.from_string(open('./keys/private.key', 'rb').read(), curve=ecdsa.SECP256k1)
        self.publicKey = ecdsa.VerifyingKey.from_string(open('./keys/public.key', 'rb').read(), curve=ecdsa.SECP256k1)

    def sign(self, message):
        return base58.b58encode(self.privateKey.sign(bytes(message, 'utf-8'))).decode('utf-8')