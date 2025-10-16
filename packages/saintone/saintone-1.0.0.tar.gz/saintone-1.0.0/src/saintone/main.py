import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

KEY = hashlib.sha256(b"bashu").digest() 
INPUT_FILE = "encode.txt"

with open(INPUT_FILE, "rb") as f:
    encoded_data = f.read()

ciphertext = base64.b64decode(encoded_data)
cipher = AES.new(KEY, AES.MODE_ECB)

try:
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    code = decrypted.decode("utf-8")
    print("")
    
    exec(code, globals())
except Exception as e:
    print("")
