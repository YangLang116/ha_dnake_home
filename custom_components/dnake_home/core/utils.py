import base64
import uuid


def encode_auth(auth_name, auth_psw):
    auth_byte = f"{auth_name}:{auth_psw}".encode("utf-8")
    return base64.b64encode(auth_byte).decode("utf-8")


def get_uuid():
    return str(uuid.uuid4())


def get_key_by_value(data: dict, test, default_value):
    return next((key for key, value in data.items() if value == test), default_value)
