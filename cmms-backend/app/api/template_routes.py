# /cmms-backend/app/api/template_routes.py
from flask import Blueprint, request, jsonify
from app.models import AssetTemplate, ComponentItem
from mongoengine.errors import NotUniqueError, DoesNotExist

# Buat Blueprint baru
template_bp = Blueprint('template_bp', __name__)

# --- GET: Mendapatkan SEMUA Template Aset ---
@template_bp.route('/templates', methods=['GET'])
def get_templates():
    try:
        templates = AssetTemplate.objects().order_by('name')
        return jsonify([t.to_json() for t in templates]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Membuat Template Aset BARU ---
@template_bp.route('/templates', methods=['POST'])
def create_template():
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('component_ids'):
            return jsonify({"error": "Nama template dan daftar ID komponen diperlukan"}), 400

        # Cari referensi ComponentItem berdasarkan ID
        component_list = []
        for comp_id in data['component_ids']:
            try:
                comp_item = ComponentItem.objects.get(id=comp_id)
                component_list.append(comp_item)
            except DoesNotExist:
                return jsonify({"error": f"Komponen {comp_id} tidak ditemukan"}), 404

        new_template = AssetTemplate(
            name=data['name'],
            components=component_list
        )
        new_template.save()
        return jsonify(new_template.to_json()), 201

    except NotUniqueError:
        return jsonify({"error": "Nama template ini sudah ada."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- PATCH: Mengupdate Template Aset (FITUR BARU) ---
@template_bp.route('/templates/<template_id>', methods=['PATCH'])
def update_template(template_id):
    try:
        data = request.get_json()
        template = AssetTemplate.objects.get(id=template_id)

        # Update Nama
        if 'name' in data:
            if data['name'] != template.name:
                # Cek unik manual jika nama berubah
                if AssetTemplate.objects(name=data['name']).first():
                    return jsonify({"error": "Nama template ini sudah ada."}), 400
            template.name = data['name']

        # Update Daftar Komponen
        if 'component_ids' in data:
            component_list = []
            for comp_id in data['component_ids']:
                try:
                    comp_item = ComponentItem.objects.get(id=comp_id)
                    component_list.append(comp_item)
                except DoesNotExist:
                    continue # Lewati jika komponen tidak ditemukan (atau return error)
            template.components = component_list

        template.save()
        return jsonify(template.to_json()), 200

    except DoesNotExist:
        return jsonify({"error": "Template tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DELETE: Menghapus Template Aset ---
@template_bp.route('/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    try:
        template = AssetTemplate.objects.get(id=template_id)
        template.delete()
        return jsonify({"message": f"Template '{template.name}' berhasil dihapus."}), 200
    except DoesNotExist:
        return jsonify({"error": "Template tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500