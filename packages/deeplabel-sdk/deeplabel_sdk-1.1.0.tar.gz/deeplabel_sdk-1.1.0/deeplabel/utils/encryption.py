import base64 
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad
def encrypt(data:str,key:str,iv:str):
    """
    Function to encrypt data using AES128 algorithm.
    data : String data
    key : 16 Char string
    iv : 16 Char string 
    """
    iv = iv.encode('utf-8')
    data= pad(data.encode(),16)
    cipher = AES.new(key.encode('utf-8'),AES.MODE_CBC,iv)
    encrypted = base64.b64encode(cipher.encrypt(data)).decode('utf-8')
    return encrypted

def decrypt(enc:str,key:str,iv:str):
    """
    Function to decrypt data using AES128 algorithm.
    data : String data
    key : 16 Char string
    iv : 16 Char string 
    """
    iv = iv.encode('utf-8')
    enc = base64.b64decode(enc)
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc),16)