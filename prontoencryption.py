import base64
import binascii

from Crypto.Cipher import AES

# these are for tests:
from Crypto.Util import Counter
import os


class ProntoEncryption:

    class ProntoEncryptionError(Exception):
        pass

    '''
    This class implements the pronto encrypt and decrypt functions.
    It is really just a wrapper around two functions to make the code a bit more portable between
    projects.
    
    A nicer implementation would have been to instantiate the class with the secret key, but
    it was important to make the function signatures exactly the same as the pronto functions 
    of the same name.
    
    Note the resultant encrypted text from encrypt is base64 encoded.
    
    Base64 is a scheme for converting binary data to printable ASCII characters,
    namely the upper- and lower-case Roman alphabet characters (A-Z, a-z), the
    numerals (0-9), and the "+" and "/" symbols, with the "=" symbol as a special
    suffix code.

    Therefore the resultant decryption may not contain any special characters other 
    than the + or the /.
    
    It is a good idea to limit the special characters that can be used in the initialization
    string.  For example, remove characters like "," or "|", "<" ">" "{" "}" so that they
    can be stored in files like an ini file where you may want to parse the text and use
    one of those characters as a separator.
    
    My first attempt was using OFB.  The pairs of encrypt_ofb and decrypt_ofb still work
    so I ahve left them in the module.
    
    Pronto uses MODE_CTR, so the encrypt and decrypt functions use MODE_CTR.
    
    '''

    @staticmethod
    def encrypt_ofb(string, key, initialisation_vector):
        if not isinstance(key, str):
            raise AttributeError('The key must be a string')
        if not isinstance(string, str):
            raise AttributeError('The string must be a string')
        if not isinstance(initialisation_vector, str):
            raise AttributeError('The initialisation vector must be a string')
        # Pronto will pad keys and vectors out to 32 characters with some internal code
        # but the code is not documented.  So we just have to enforce these to be 32 characters.
        if len(key) < 32:
            raise AttributeError('The key must be at least 32 characters long')
        if len(initialisation_vector) < 16:
            raise AttributeError('The initialisation vector must be at least 16 characters long')
        # trim anything over 32 and 16 respectively
        key = key[0:32]
        initialisation_vector = initialisation_vector[0:16]
        cipher = AES.new(bytes(key, 'UTF-8'), AES.MODE_OFB, iv=bytes(initialisation_vector, 'UTF-8'))
        ciphertext = cipher.encrypt(bytes(string, 'UTF-8'))
        return base64.b64encode(ciphertext)

    @staticmethod
    def decrypt_ofb(encryptedstring, key, initialisation_vector):
        if not isinstance(key, str):
            raise AttributeError('The key must be a string')
        if not isinstance(encryptedstring, str):
            raise AttributeError('The string must be a string')
        if not isinstance(initialisation_vector, str):
            raise AttributeError('The initialisation vector must be a string')
        # Pronto will pad keys and vectors out to 32 characters with some internal code
        # but the code is not documented.  So we just have to enforce these to be 32 characters.
        if len(key) < 32:
            raise AttributeError('The key must be at least 32 characters long')
        if len(initialisation_vector) < 16:
            raise AttributeError('The initialisation vector must be at least 16 characters long ({})'.format(
                len(initialisation_vector)))
        # trim anything over 32 and 16 respectively
        key = key[0:32]
        initialisation_vector = initialisation_vector[0:16]
        # Mode_ofb is the nearest
        cipher = AES.new(bytes(key, 'UTF-8'), AES.MODE_OFB, iv=bytes(initialisation_vector, 'UTF-8'))
        ciphertext = base64.b64decode(encryptedstring)
        # At this stage ciphertext should be a bytes array
        return cipher.decrypt(ciphertext).decode('UTF-8')

    @staticmethod
    def __int_of_string(s):
        # x =  binascii.hexlify(bytes(s,'UTF-8'))
        # return int(binascii.hexlify(bytes(s,'UTF-8'),16))
        return int(binascii.hexlify(bytes(s,'UTF-8')),16)

    def encrypt(string, key, initialisation_vector):
        if not isinstance(key, str):
            raise AttributeError('The key must be a string')
        if not isinstance(string, str):
            raise AttributeError('The string must be a string')
        if not isinstance(initialisation_vector, str):
            raise AttributeError('The initialisation vector must be a string')
        # Pronto will pad keys and vectors out to 32 characters with some internal code
        # but the code is not documented.  So we just have to enforce these to be 32 characters.
        if len(key) < 32:
            raise AttributeError('The key must be at least 32 characters long')
        if len(initialisation_vector) < 16:
            raise AttributeError('The initialisation vector must be at least 16 characters long')
        # trim anything over 32 and 16 respectively
        key = key[0:32]
        initialisation_vector = initialisation_vector[0:16]
        thiscounter = Counter.new(128,initial_value=ProntoEncryption.__int_of_string(initialisation_vector))
        cipher = AES.new(bytes(key, 'UTF-8'), AES.MODE_CTR, counter=thiscounter)
        ciphertext = cipher.encrypt(bytes(string, 'UTF-8'))
        return base64.b64encode(ciphertext)


    @staticmethod
    def decrypt(encryptedstring, key, initialisation_vector):
        if not isinstance(key, str):
            raise AttributeError('The key must be a string')
        if not isinstance(encryptedstring, str):
            raise AttributeError('The string must be a string')
        if not isinstance(initialisation_vector, str):
            raise AttributeError('The initialisation vector must be a string')
        # Pronto will pad keys and vectors out to 32 characters with some internal code
        # but the code is not documented.  So we just have to enforce these to be 32 characters.
        if len(key) < 32:
            raise AttributeError('The key must be at least 32 characters long')
        if len(initialisation_vector) < 16:
            raise AttributeError('The initialisation vector must be at least 16 characters long ({})'.format(
                len(initialisation_vector)))
        # trim anything over 32 and 16 respectively
        key = key[0:32]
        initialisation_vector = initialisation_vector[0:16]
        thiscounter = Counter.new(128,initial_value=ProntoEncryption.__int_of_string(initialisation_vector))
        cipher = AES.new(bytes(key, 'UTF-8'), AES.MODE_CTR, counter=thiscounter)
        try:
            ciphertext = base64.b64decode(encryptedstring)
        except Exception as e:
            print('Print could not decode the encrypted text {}'.format(str(e)))
        # At this stage ciphertext should be a bytes array
        # print("Ciphertext is of type {}".format(type(ciphertext)))
        # print("Hex of Cipher is {}".format(ciphertext.hex()))
        decrypted = cipher.decrypt(ciphertext)
        # "decrypted" is a bytes array
        # to convert it into a string we decode it.
        # print("decryption is {}".format(decrypted.decode('UTF-8')))
        # print("-------------------------------------------------------")
        return decrypted.decode('UTF-8')
