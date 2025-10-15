import unittest
import pyseapc
from OpenSSL import crypto
import os

privateKeyName = os.path.join(os.getcwd(), 'exposed_private_key.pem')
publicKeyName = os.path.join(os.getcwd(), 'certificate.crt')
generatedPrivateKeyName = os.path.join(os.getcwd(), 'private_key.pem')

def generate_keys():

    # Create key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Create self-signed certificate
    cert = crypto.X509()
    cert.get_subject().C = "??"
    cert.get_subject().ST = "any"
    cert.get_subject().L = "any"
    cert.get_subject().O = "any"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha256")

    print('Saving generated SSL keys to ', os.getcwd())
    print('\tPrivate Key: ', os.path.join(privateKeyName))
    print('\tCertificate: ', os.path.join(publicKeyName))
    print('These files must be stored securely for the communication with APC to be secure.\n')

    # Write private key and certificate to files
    with open(privateKeyName, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    with open(publicKeyName, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    return [crypto.dump_privatekey(crypto.FILETYPE_PEM, key), crypto.dump_certificate(crypto.FILETYPE_PEM, cert)]


class TestInterface(unittest.TestCase):
    def test_create_environment_generate_keys(self):
        app = pyseapc.ApcExternalPythonEnvironment(min, generate_ssl_keys=True)
    
    def test_create_environment_load_keys(self):
        generate_keys()
        app = pyseapc.ApcExternalPythonEnvironment(min, private_key_path=privateKeyName,
                                                        public_key_path=publicKeyName)
        os.remove(privateKeyName)
        os.remove(publicKeyName)
        os.remove(generatedPrivateKeyName)

    def test_no_keys_given(self):
        with self.assertRaises(ValueError):
            app = pyseapc.ApcExternalPythonEnvironment(min)