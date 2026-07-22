# /cmms-backend/app/decorators.py
from flask import request

TOKEN_PREFIX = "MOCK_TOKEN_SESUAI_ROLE_"

def get_role_from_request():
    """Ambil role pemanggil dari header 'Authorization: Bearer MOCK_TOKEN_SESUAI_ROLE_<ROLE>'.
    Mengembalikan role dalam huruf kecil, atau None kalau header tidak ada/tidak sesuai format."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[len('Bearer '):].strip()
    if not token.startswith(TOKEN_PREFIX):
        return None
    role = token[len(TOKEN_PREFIX):].strip().lower()
    return role or None
