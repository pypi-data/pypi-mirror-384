from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import json

import logging

l = logging.getLogger(__name__)

from .jsonutils import jsonwalker


class CASTTABLE:
    __code2type = {0: str, 1: int, 2: float}

    __type2code = {
        int: 1,
        float: 2,
    }

    @staticmethod
    def gettype(code):
        return CASTTABLE.__code2type.get(int(code), str)

    @staticmethod
    def getcode(datatype):
        code = CASTTABLE.__type2code.get(datatype, None)
        if code is None:
            return ""
        return str(code).rjust(2, "0")

    # def getencoded(value,encrypted):
    #     code = CASTTABLE.getcode(value)
    #     if code:
    #         return "$".join([code,encrypted])

    # def getdecoded(value):
    #     parts = "$".split(value)
    #     if len(parts)==2:
    #         casttype = CASTTABLE.get(int(parts[0] ),str)
    #     decrypted_value = casttype(self.engine.decrypt(parts[-1]))
    #     return decrypted_value


class CryptUtil:
    def __init__(
        self,
        key=None,
        engine=None,
        padding=None,
    ) -> None:
        self._key = key
        if not engine:
            engine = AesEngine
        self.engine = engine()
        if isinstance(self.engine, AesEngine):
            self.engine._set_padding_mechanism(padding)

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    def _update_key(self):
        key = self._key() if callable(self._key) else self._key
        self.engine._update_key(key)

    def encryptval(self, value, preformat=None, postformat=None) -> str:
        """
        try to encrypt the value, regardless of what it is. Adds a CODE$ at the beginning if a number type is recognised to allow cast back
        """
        try:
            self._update_key()
            v = self.engine.encrypt(value if preformat is None else preformat(value))
            if code := CASTTABLE.getcode(type(value)):
                v = code + "$" + v
            return v if postformat is None else postformat(v)

        except Exception as e:
            l.exception(f"******************exception while processing {value}:\n{e}")
            return ""

    def decryptval(self, value):
        """
        Stringify value, try to get 'CODE$' part, decrypt the rest of the string and cast it according to CODE, if present
        """
        self._update_key()
        parts = str(value).split(
            "$"
        )  # value should already be a str, but plain uncrypted object may be other things
        casttype = None
        if len(parts) == 2:
            casttype = CASTTABLE.gettype(int(parts[0]))
        try:
            decrypted_value = self.engine.decrypt(parts[-1])
        except Exception as e:
            # can't decrypt, it was a old plain value
            l.debug("can't decrypt, sending back the plain value")
            return value

        if casttype:
            decrypted_value = casttype(decrypted_value)
        return decrypted_value

    def encryptRecursive(
        self, value, preformat=None, postformat=None, skip_keys: list = []
    ) -> str:
        """
        Recursively walk through value and crypt elemets separately and json dump it to string
        """
        self._update_key()
        w = jsonwalker(
            lambda val: self.encryptval(val, preformat, postformat), skip_keys
        )
        newstruct = json.dumps(w.walk(value))
        # l.debug(f"encrypted in {newstruct}")
        return newstruct

    def decryptRecursive(self, value, skip_keys: list = []):
        """
        JSON parse Value and recursively walk through it and decrypt elemets separately
        """
        w = jsonwalker(self.decryptval, skip_keys)
        try:
            val = json.loads(value)
        except Exception as e:
            val = {}
            if value:
                l.info(f"exception decrypting {value}:{e}")
        newstruct = w.walk(val)
        return newstruct


from Crypto.Cipher import AES
from Crypto import Random
import hashlib
import binascii

from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy.dialects.mysql import CHAR

class MySQLCryptUtil:
    def __init__(self, key=None) -> None:
        self.sha2_key_hexed = self.sql_unhex_sha2(key).hex()
        self.mysql_key = self.mysql_aes_key(self.sha2_key_hexed)
        self.cipher = AES.new(self.mysql_key, AES.MODE_ECB)
        
    
    def mysql_aes_key(self, key) -> bytes:
        final_key = bytearray(16)
        for i, c in enumerate(key):
            final_key[i % 16] ^= ord(key[i])
        return bytes(final_key)

    def mysql_aes_val(self, val) -> str:
        pad_value = 16 - (len(val) % 16)
        return "%s%s" % (val, chr(pad_value) * pad_value)

    def mysql_aes_encrypt(self, val) -> bytes:
        v = self.mysql_aes_val(val)
        return self.cipher.encrypt(v.encode(encoding="utf-8"))

    def mysql_aes_decrypt(self, val) -> str:
        
        return (
            self.cipher.decrypt(val)
            .decode(encoding="utf-8")
            .rstrip("\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10")
        )

    def sql_unhex_sha2(self, input_string, bits=512) -> bytes:
        # First create SHA-512 hash (equivalent to SHA2 in SQL)
        hash_obj = hashlib.sha512(input_string.encode("utf-8"))
        hex_digest = hash_obj.hexdigest()

        # Convert hex to binary (equivalent to UNHEX in SQL)
        binary_result = binascii.unhexlify(hex_digest)

        return binary_result
    
    def encrypt(self, value, hexed=True, upper=True):
        encrypted = self.mysql_aes_encrypt(value)
        if hexed:
            encrypted = encrypted.hex()
            if upper:
                encrypted = encrypted.upper()
        return encrypted

    def decrypt(self, value, hexed=True):
        if hexed:
            value = bytes.fromhex(value)
        encrypted = self.mysql_aes_decrypt(value)
        return encrypted
    
    @staticmethod
    def aes_decrypt_func(col, key):
        return cast(
            func.aes_decrypt(
                func.unhex(col),
                func.sha2(key, 512),
            ),
            CHAR(charset="utf8"),
        )
# usage
# print("select LOWER(HEX(AES_ENCRYPT('my data','some key')));")
# print(mysql_aes_encrypt("my data", "some key").hex())
