import os
import sys
import traceback
from concurrent import futures

from OpenSSL import crypto
import grpc
from google.protobuf.struct_pb2 import Value
from google.protobuf import json_format

from pyseapc.ExternalPythonInterface_pb2 import ExternalPythonCallResponse, ExternalPythonCallStatus, ExternalPythonCallStatusCode
from pyseapc.ExternalPythonInterface_pb2_grpc import add_ExternalPythonCallServicer_to_server, ExternalPythonCallServicer

private_key_file_name = "private_key.pem"
public_key_file_name = "certificate.crt"

class SuppressStream(object): 
    """A simple class for suppressing undesired messages to StdErr during its existence"""
    
    # Allows suppressing false warning messages from a dependency of gRPC (ABSL) 
    def __init__(self):
        self.orig_stream_fileno = sys.stderr.fileno()

    def __enter__(self):
        self.orig_stream_dup = os.dup(self.orig_stream_fileno)
        self.devnull = open(os.devnull, 'w')
        os.dup2(self.devnull.fileno(), self.orig_stream_fileno)

    def __exit__(self, type, value, traceback):
        os.close(self.orig_stream_fileno)
        os.dup2(self.orig_stream_dup, self.orig_stream_fileno)
        os.close(self.orig_stream_dup)
        self.devnull.close()

class GrpcServer(ExternalPythonCallServicer):
    server_version = "1.0.0"

    def __init__(self, user_method):
        self.user_method = user_method 

    def SyncCall(self, request, context):
        try:
            inputData = json_format.MessageToDict(request.input)
            results = self.user_method(inputData)
            resultValue = Value()
            json_format.ParseDict(results, resultValue)

            details = {}
            detailsValue = Value()
            json_format.ParseDict(details, detailsValue)
            
            status = ExternalPythonCallStatus(
                statusCode=ExternalPythonCallStatusCode.STATUS_GOOD, 
                message='Success',
                details=detailsValue
            )

            response = ExternalPythonCallResponse(
                output=resultValue, status=status, version = self.server_version)
            return  response
        except Exception as e:
            print('\nException occured while handling remote Python user code:\n', e, traceback.print_exc())

            results = None
            resultValue = Value()
            json_format.ParseDict(results, resultValue)

            details = {'traceback': str(traceback.print_exc())}
            detailsValue = Value()
            json_format.ParseDict(details, detailsValue)
            
            status = ExternalPythonCallStatus(
                statusCode=ExternalPythonCallStatusCode.STATUS_ERROR_NO_USER_CODE_RESPONSE, 
                message=  '{}: {}'.format(type(e).__name__, e),
                details=detailsValue
            )

            response = ExternalPythonCallResponse(
                output=resultValue, status=status, version = self.server_version)
            return response
        
    def Ping(self, request, context):
        # Simply return what was passed
        resultValue = request.input

        details = {}
        detailsValue = Value()
        json_format.ParseDict(details, detailsValue)
        
        status = ExternalPythonCallStatus(
            statusCode=ExternalPythonCallStatusCode.STATUS_GOOD, 
            message='Success',
            details=detailsValue
        )

        response = ExternalPythonCallResponse(
            output=resultValue, status=status, version = self.server_version)
        return response

class ApcExternalPythonEnvironment(object):
    """An External Python Environment for Schneider Electric APC

    This class faciliatates mixing user logic defined in the Python environment
    it is launched from to be used from within APC director scripts. This allows 
    the user to make use of packages and resources typically unavailable from
    within a Director script such as popular Python packages (numpy, pandas,
    tensorflow, etc.), local files and resources and other APIs.

    Internally this is facilitated through gRPC where this class is a gRPC 
    server and the Director code in APC is a gRPC client.

    Methods
    -------
    start(port: int, wait_for_termination: bool=True)
        Starts the external Python environment on a given port, optionally waiting for termination.
    """
    
    def __init__(self, user_method, private_key_path: str=None, public_key_path: str=None, generate_ssl_keys: bool=False):
        """Initialize the external Python environment

        The signature of the user_method should only have one argument and the
        argument and return values are what will be passed in and returned in 
        the corresponding "CallRemotePython" call in Director. The argument and
        return value can be any valid combination of list, int, float, str and
        dict. More complex objects like numpy arrays, dataframes and custom 
        objects should be simplified. 

        Either both the public and private keys must be provided or 
        generate_ssl_keys must be True or a ValueError will be raised.
        
        Paramters
        ---------
        user_method: function
            The user logic that should be executed when "CallRemotePython" is executed in Director.
        private_key_path: str, optional
            Path to the private key for SSL/TLS. Defaults to None
        public_key_path: str, optional
            Path to the public key for SSL/TLS. Defaults to None
        generate_ssl_keys: bool, optional
            Whether the SSL/TLS keys should be automatically generated. This overrides any key paths provided. Defaults to False.
        """
        
        self.user_method = user_method
        self.callback = None
        self.private_key = None
        self.public_key = None
        self.public_key_path = public_key_path
        self.using_generated_ssl_cert = False

        if (private_key_path is None or public_key_path is None) and not generate_ssl_keys:
            raise ValueError("Either both the public and private keys must be provided or generate_ssl_keys must be true")

        if generate_ssl_keys:
            self.private_key, self.public_key = self._generate_keys()
            self.using_generated_ssl_cert = True
        else:
            with open(private_key_path, 'rb') as f:
                self.private_key = f.read()
            with open(public_key_path, 'rb') as f:
                self.public_key = f.read()
            self.using_generated_ssl_cert = False

    def _generate_keys(self):
        """Generate new private and public SSL/TLS keys for excrypting the connection with APC
        
        Returns
        -------
        list
            Two elements: [private key contents, public key contents]
        """

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
        print('\tPrivate Key: ', os.path.join(os.getcwd(), private_key_file_name))
        print('\tCertificate: ', os.path.join(os.getcwd(), public_key_file_name))
        print('These files must be stored securely for the communication with APC to be secure.\n')

        # Write private key and certificate to files
        with open(private_key_file_name, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

        with open(public_key_file_name, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        self.public_key_path = os.path.join(os.getcwd(), public_key_file_name)

        return [crypto.dump_privatekey(crypto.FILETYPE_PEM, key), crypto.dump_certificate(crypto.FILETYPE_PEM, cert)]

    def start(self, port: int, wait_for_termination: bool=True):
        """Starts the external Python environment on a given port, optionally waiting for termination.

        Parameters
        ----------
        port: int
            The port on the local machine to use for hosting the environment
        wait_for_termination: bool, optional
            Whether to block the process to keep the environment running (defaults to True)
        """

        # Start up the gRPC server at the requested URL while suppressing false errors
        with SuppressStream():
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ExternalPythonCallServicer_to_server(GrpcServer(self.user_method), server)
        credentials = grpc.ssl_server_credentials([[self.private_key, self.public_key], ])
        try:
            server.add_secure_port(f'[::]:{port}', credentials)
            server.start()
            print(f"External Python environment server running on https://localhost:{port}")
            if self.using_generated_ssl_cert:
                print("Using internally-generated and signed SSL certificate. APC will need this to connect securely to this environment.")
                print(self.public_key.decode('utf-8'))
            else:
                print("Using the following public key for SSL: ", self.public_key_path)
            if wait_for_termination:
                server.wait_for_termination()
        except KeyboardInterrupt:
            print("Closing due to keyboard interrupt...")
        except Exception as e:
            print("Fatal Server Error: ", e)