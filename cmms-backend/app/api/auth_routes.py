# /cmms-backend/app/api/auth_routes.py
from flask import Blueprint, request, jsonify
from app.models import User
from mongoengine.errors import DoesNotExist, NotUniqueError

auth_bp = Blueprint('auth_bp', __name__)

# --- POST: Rute Login ---
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email dan password diperlukan."}), 400

        # 1. Cari pengguna
        user = User.objects(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({"error": "Email atau password salah."}), 401

        # 2. Autentikasi Berhasil
        return jsonify({
            "user_id": str(user.id),
            "name": user.name,
            "role": user.role,
            "token": "MOCK_TOKEN_SESUAI_ROLE_" + user.role.upper() 
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Rute Registrasi ---
@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'technician') # Default ke technician

        if not name or not email or not password:
            return jsonify({"error": "Nama, email, dan password diperlukan."}), 400
        
        # 1. Tentukan Role
        # Jika belum ada user di DB (pertama kali registrasi), user ini OTOMATIS jadi admin.
        user_count = User.objects.count()
        final_role = 'admin' if user_count == 0 else role.lower()
        
        # 2. Buat User baru (dengan hashing password)
        new_user = User(name=name, email=email, role=final_role)
        new_user.set_password(password) # Panggil setter Bcrypt
        
        new_user.save()
        
        # 3. Autentikasi setelah registrasi berhasil
        return jsonify({
            "user_id": str(new_user.id),
            "name": new_user.name,
            "role": new_user.role,
            "token": "MOCK_TOKEN_SESUAI_ROLE_" + new_user.role.upper()
        }), 201

    except NotUniqueError:
        return jsonify({"error": "Email sudah terdaftar. Gunakan email unik."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400