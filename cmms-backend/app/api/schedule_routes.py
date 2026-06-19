# /cmms-backend/app/api/schedule_routes.py
from flask import Blueprint, request, jsonify
from app.models import MaintenanceSchedule, Asset
from mongoengine.errors import DoesNotExist
import datetime

# Buat Blueprint baru
schedule_bp = Blueprint('schedule_bp', __name__)

# --- GET: Mendapatkan SEMUA Jadwal (dengan Iterasi Aman) ---
@schedule_bp.route('/schedules', methods=['GET'])
def get_schedules():
    try:
        # Urutkan berdasarkan tanggal jatuh tempo terdekat
        schedules_raw = MaintenanceSchedule.objects().order_by('next_due_date')
        
        safe_schedules = []
        for s in schedules_raw:
            try:
                safe_schedules.append(s.to_json())
            except Exception:
                print(f"SKIPPING corrupted schedule: {s.id}")
                continue 
                
        return jsonify(safe_schedules), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Membuat Jadwal BARU ---
@schedule_bp.route('/schedules', methods=['POST'])
def create_schedule():
    try:
        data = request.get_json()
        
        if not data.get('asset_id') or not data.get('task_name') or not data.get('frequency_days'):
            return jsonify({"error": "Input tidak lengkap: asset_id, task_name, dan frequency_days diperlukan"}), 400

        # Cari Aset
        try:
            asset = Asset.objects.get(id=data['asset_id'])
        except DoesNotExist:
            return jsonify({"error": "Aset tidak ditemukan"}), 404

        # Validasi Frekuensi
        try:
            days = int(data['frequency_days'])
            if days <= 0:
                raise ValueError("Hari harus lebih dari 0")
        except (ValueError, TypeError):
             return jsonify({"error": "frequency_days harus angka positif"}), 400
        
        # Hitung Tanggal Jatuh Tempo
        start_date_str = data.get('start_date')
        if start_date_str:
             start_date = datetime.datetime.fromisoformat(start_date_str)
        else:
             start_date = datetime.datetime.utcnow()

        next_due = start_date + datetime.timedelta(days=days)

        # Buat objek Jadwal baru
        new_schedule = MaintenanceSchedule(
            asset=asset,
            task_name=data['task_name'],
            frequency=data.get('frequency', f'Setiap {days} hari'), 
            frequency_days=days,
            next_due_date=next_due,
            description_template=data.get('description_template', ''),
            component=data.get('component', '') 
        )
        
        new_schedule.save()
        
        return jsonify(new_schedule.to_json()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- PATCH: Update Jadwal (Edit) ---
@schedule_bp.route('/schedules/<schedule_id>', methods=['PATCH'])
def update_schedule(schedule_id):
    try:
        data = request.get_json()
        schedule = MaintenanceSchedule.objects.get(id=schedule_id)

        if 'task_name' in data:
            schedule.task_name = data['task_name']
        
        if 'description_template' in data:
            schedule.description_template = data['description_template']
            
        if 'component' in data:
            schedule.component = data['component']

        # Jika asset berubah
        if 'asset_id' in data:
             try:
                 new_asset = Asset.objects.get(id=data['asset_id'])
                 schedule.asset = new_asset
             except DoesNotExist:
                 return jsonify({"error": "Aset baru tidak ditemukan"}), 404

        # Jika frekuensi berubah, kita update data frekuensi.
        # NOTE: Kita TIDAK mereset next_due_date secara otomatis saat edit agar tidak mengacaukan jadwal berjalan,
        # kecuali user nanti meminta fitur reset tanggal.
        if 'frequency_days' in data:
            try:
                days = int(data['frequency_days'])
                if days <= 0: raise ValueError
                schedule.frequency_days = days
                schedule.frequency = f"Setiap {days} hari"
            except:
                return jsonify({"error": "Frequency days invalid"}), 400

        schedule.save()
        return jsonify(schedule.to_json()), 200

    except DoesNotExist:
        return jsonify({"error": "Jadwal tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Tandai Jadwal Selesai (Maju ke Siklus Berikutnya) ---
@schedule_bp.route('/schedules/<schedule_id>/complete', methods=['POST'])
def complete_schedule(schedule_id):
    try:
        schedule = MaintenanceSchedule.objects.get(id=schedule_id)
        now = datetime.datetime.utcnow()
        schedule.next_due_date = now + datetime.timedelta(days=schedule.frequency_days)
        schedule.save()
        return jsonify(schedule.to_json()), 200
    except DoesNotExist:
        return jsonify({"error": "Jadwal tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DELETE: Hapus Jadwal ---
@schedule_bp.route('/schedules/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    try:
        schedule = MaintenanceSchedule.objects.get(id=schedule_id)
        schedule.delete()
        return jsonify({"message": f"Jadwal '{schedule.task_name}' berhasil dihapus."}), 200

    except DoesNotExist:
        return jsonify({"error": "Jadwal tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500