# /cmms-backend/app/api/compliance_routes.py
from flask import Blueprint, request, jsonify
from app.models import ComplianceLog, Asset 
from mongoengine.errors import DoesNotExist
import datetime

# Buat Blueprint baru
compliance_bp = Blueprint('compliance_bp', __name__)

# --- GET: Mendapatkan SEMUA Log Kepatuhan ---
@compliance_bp.route('/logs', methods=['GET'])
def get_compliance_logs():
    try:
        logs = ComplianceLog.objects().order_by('next_check_due')
        return jsonify([log.to_json() for log in logs]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST: Membuat Log Kepatuhan BARU ---
@compliance_bp.route('/logs', methods=['POST'])
def create_compliance_log():
    try:
        data = request.get_json()
        
        if not data.get('asset_id') or not data.get('regulation_name'):
            return jsonify({"error": "Input tidak lengkap: asset_id dan regulation_name diperlukan"}), 400

        # Cari Aset
        try:
            asset = Asset.objects.get(id=data['asset_id'])
        except DoesNotExist:
            return jsonify({"error": "Aset tidak ditemukan"}), 404

        # Handle next_check_due date
        next_due = None
        if data.get('next_check_due'):
            try:
                next_due_date_only = datetime.datetime.fromisoformat(data['next_check_due'])
                next_due = next_due_date_only.replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                 return jsonify({"error": "Format next_check_due salah."}), 400
        
        # Buat Log Kepatuhan baru
        new_log = ComplianceLog(
            asset=asset,
            regulation_name=data['regulation_name'],
            status=data.get('status', 'pending'),
            next_check_due=next_due,
            evidence_document_url=data.get('evidence_document_url', '')
        )
        
        new_log.save()
        
        return jsonify(new_log.to_json()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- GET Compliance Stats ---
@compliance_bp.route('/stats', methods=['GET'])
def get_compliance_stats():
    try:
        overdue_count = ComplianceLog.objects(status='overdue').count()
        pending_count = ComplianceLog.objects(status='pending').count()
        
        return jsonify({
            "overdue_count": overdue_count,
            "pending_count": pending_count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RUTE BARU: PATCH (Update Status) Log Kepatuhan ---
@compliance_bp.route('/logs/<log_id>', methods=['PATCH'])
def update_compliance_log(log_id):
    try:
        data = request.get_json()
        log = ComplianceLog.objects.get(id=log_id)
        
        if 'status' in data:
            new_status = data['status'].lower()
            allowed_statuses = ['pending', 'compliant', 'overdue']
            
            if new_status not in allowed_statuses:
                return jsonify({"error": "Status tidak valid."}), 400
            
            log.status = new_status
            log.save()
            
            return jsonify(log.to_json()), 200
        
        return jsonify({"message": "Tidak ada data yang diupdate"}), 200

    except DoesNotExist:
        return jsonify({"error": "Log Kepatuhan tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500