import base64
import uuid


def encode_auth(auth_name, auth_psw):
    auth_byte = f'{auth_name}:{auth_psw}'.encode('utf-8')
    return base64.b64encode(auth_byte).decode('utf-8')


def get_uuid():
    return str(uuid.uuid4())
