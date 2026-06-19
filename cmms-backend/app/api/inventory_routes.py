# /cmms-backend/app/api/inventory_routes.py
from flask import Blueprint, request, jsonify
from app.models import ComponentItem
from mongoengine.errors import NotUniqueError, DoesNotExist

# Buat Blueprint baru
inventory_bp = Blueprint('inventory_bp', __name__)

# --- GET: Mendapatkan SEMUA Komponen di Gudang ---
@inventory_bp.route('/components', methods=['GET'])
def get_components():
    try:
        components = ComponentItem.objects().order_by('name')
        return jsonify([c.to_json() for c in components]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Membuat Komponen BARU ---
@inventory_bp.route('/components', methods=['POST'])
def create_component():
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('stock_quantity'):
            return jsonify({"error": "Nama dan Kuantitas Stok diperlukan"}), 400

        new_comp = ComponentItem(
            name=data['name'],
            part_number=data.get('part_number', ''),
            stock_quantity=int(data['stock_quantity']),
            location=data.get('location', 'Gudang Utama')
        )
        new_comp.save()
        return jsonify(new_comp.to_json()), 201

    except NotUniqueError:
        return jsonify({"error": "Komponen dengan nama ini sudah ada."}), 400
    except (ValueError, TypeError):
         return jsonify({"error": "Kuantitas Stok harus berupa angka."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- PATCH: Mengupdate Komponen (terutama Stok) ---
@inventory_bp.route('/components/<item_id>', methods=['PATCH'])
def update_component(item_id):
    try:
        data = request.get_json()
        comp = ComponentItem.objects.get(id=item_id)

        if 'name' in data:
            comp.name = data['name']
        if 'part_number' in data:
            comp.part_number = data['part_number']
        if 'stock_quantity' in data:
            comp.stock_quantity = int(data['stock_quantity'])
        if 'location' in data:
            comp.location = data['location']
            
        comp.save()
        return jsonify(comp.to_json()), 200

    except DoesNotExist:
        return jsonify({"error": "Komponen tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DELETE: Menghapus Komponen ---
@inventory_bp.route('/components/<item_id>', methods=['DELETE'])
def delete_component(item_id):
    try:
        comp = ComponentItem.objects.get(id=item_id)
        # TODO: Cek dulu apakah komponen ini sedang digunakan oleh Aset
        # (Untuk saat ini, kita izinkan hapus)
        comp.delete()
        return jsonify({"message": f"Komponen '{comp.name}' berhasil dihapus."}), 200
    except DoesNotExist:
        return jsonify({"error": "Komponen tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500