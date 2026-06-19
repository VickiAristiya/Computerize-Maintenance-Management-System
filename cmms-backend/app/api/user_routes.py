# /cmms-backend/app/api/user_routes.py
from flask import Blueprint, request, jsonify
from app.models import User
from mongoengine.errors import NotUniqueError, DoesNotExist

# Buat Blueprint baru
user_bp = Blueprint('user_bp', __name__)

# --- GET: Mendapatkan SEMUA User ---
@user_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.objects().order_by('role', 'name')
        safe_users = []
        for user in users:
            user_data = user.to_json()
            # Hapus password hash dari respons untuk keamanan
            if 'password' in user_data:
                del user_data['password']
            safe_users.append(user_data)
            
        return jsonify(safe_users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Membuat User BARU ---
@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'technician')

        if not name or not email or not password or not role:
            return jsonify({"error": "Nama, email, password, dan role diperlukan."}), 400
        
        allowed_roles = ['admin', 'manager', 'technician']
        if role.lower() not in allowed_roles:
            return jsonify({"error": "Role tidak valid."}), 400

        # Buat User baru (dengan hashing password)
        new_user = User(name=name, email=email, role=role.lower())
        new_user.set_password(password) # Panggil setter Bcrypt
        
        new_user.save()
        
        return jsonify(new_user.to_json()), 201

    except NotUniqueError:
        return jsonify({"error": "Email sudah terdaftar. Gunakan email unik."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- DELETE: Menghapus User ---
@user_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return jsonify({"message": f"Pengguna '{user.name}' berhasil dihapus."}), 200
    except DoesNotExist:
        return jsonify({"error": "Pengguna tidak ditemukan."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- PATCH: Mengupdate Detail dan Role User ---
@user_bp.route('/users/<user_id>', methods=['PATCH'])
def update_user(user_id):
    try:
        data = request.get_json()
        user = User.objects.get(id=user_id) # Cari user yang mau diupdate

        if 'name' in data: 
            user.name = data['name']
            
        if 'email' in data and data['email'] != user.email:
            # Pengecekan unik saat email diubah
            if User.objects(email=data['email']).count() > 0:
                 return jsonify({"error": "Email sudah terdaftar oleh pengguna lain."}), 400
            user.email = data['email']
            
        if 'role' in data:
            allowed_roles = ['admin', 'manager', 'technician']
            if data['role'].lower() not in allowed_roles:
                return jsonify({"error": "Role tidak valid."}), 400
            user.role = data['role'].lower()
            
        if 'password' in data and data['password']:
            # Reset password
            user.set_password(data['password'])
            
        user.save()
        return jsonify(user.to_json()), 200

    except DoesNotExist:
        return jsonify({"error": "Pengguna tidak ditemukan."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400