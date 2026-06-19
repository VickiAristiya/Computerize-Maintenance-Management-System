# /cmms-backend/app/api/dashboard_routes.py
from flask import Blueprint, jsonify
from app.models import Asset, WorkOrder, MaintenanceSchedule, ComponentItem, SensorData
from app.ml_service import CompressorPredictor
import datetime
import math

dashboard_bp = Blueprint('dashboard_bp', __name__)
predictor = CompressorPredictor()


def _sensor_to_payload(sensor_data):
    payload = {}
    for column in predictor.feature_columns:
        payload[column] = getattr(sensor_data, column, None)
    payload["demo_mode"] = getattr(sensor_data, "demo_mode", None)
    return payload

def get_predictive_maintenance_notifications():
    """Fungsi untuk mendapatkan notifikasi predictive maintenance"""
    notifications = []

    if not predictor.is_ready():
        return notifications

    try:
        # Ambil semua asset
        assets = Asset.objects()

        for asset in assets:
            # Ambil data sensor terbaru untuk asset ini
            latest_sensor = SensorData.objects(asset=asset).order_by('-timestamp').first()

            if latest_sensor:
                prediction = predictor.predict(_sensor_to_payload(latest_sensor))
                if not prediction["ok"]:
                    continue

                is_demo_maintenance = str(prediction.get("demo_mode") or "").startswith("maintenance")

                # Buat notifikasi berdasarkan prediksi.
                # Mode demo maintenance selalu dimunculkan agar tombol rendah/sedang/tinggi/kritis
                # bisa dipakai untuk presentasi alur predictive maintenance.
                if is_demo_maintenance or prediction['failure_probability'] > 0.3:
                    notifications.append({
                        "id": f"pred-{str(asset.id)}",
                        "asset_id": str(asset.id),
                        "asset_name": asset.name,
                        "demo_mode": prediction.get("demo_mode"),
                        "risk_level": prediction.get("risk_level"),
                        "type": "predictive_maintenance",
                        "title": "Prediksi Maintenance Diperlukan",
                        "message": prediction['recommendation'],
                        "priority": prediction['priority'],
                        "due_date": prediction['due_date'],
                        "predicted_days": prediction['predicted_days'],
                        "failure_probability": prediction['failure_probability'],
                        "health_score": prediction['health_score'],
                        "link": "/work-orders"  # Link ke halaman work orders untuk membuat WO
                    })

        # Sort by priority (critical > high > medium > low) dan failure probability
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        notifications.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['failure_probability']), reverse=True)

        # Ambil hanya 10 notifikasi teratas
        return notifications[:10]

    except Exception as e:
        print(f"Error getting predictive notifications: {e}")
        return notifications

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        # --- 1. Statistik Aset ---
        total_assets = Asset.objects.count()
        down_assets = Asset.objects(status='down').count()
        
        # --- 2. Statistik Inventaris (NEW) ---
        total_components = ComponentItem.objects.count()
        # Hitung komponen dengan stok < 5
        low_stock_components = ComponentItem.objects(stock_quantity__lt=5).count()
        
        # --- 3. Statistik WO ---
        open_wo = WorkOrder.objects(status='open').count()
        in_progress_wo = WorkOrder.objects(status='in_progress').count()
        pending_verif_wo = WorkOrder.objects(status='pending_verification').count()
        completed_wo = WorkOrder.objects(status='completed').count()
        
        # --- 4. Jadwal Perawatan Terlewat dan Mendekati ---
        today = datetime.datetime.utcnow()
        next_week = today + datetime.timedelta(days=7)

        upcoming_schedules_raw = MaintenanceSchedule.objects(
            next_due_date__lte=next_week
        ).order_by('next_due_date')

        upcoming_schedules = []
        for sch in upcoming_schedules_raw:
            delta = sch.next_due_date - today
            days_left = math.ceil(delta.total_seconds() / 86400)
            schedule_status = "overdue" if days_left < 0 else "due_today" if days_left == 0 else "upcoming"

            upcoming_schedules.append({
                "id": str(sch.id),
                "task_name": sch.task_name,
                "asset_name": sch.asset.name if sch.asset else "Unknown Asset",
                "due_date": sch.next_due_date.isoformat(),
                "days_left": days_left,
                "status": schedule_status,
                "priority": "high" if days_left <= 3 or schedule_status == "overdue" else "medium"
            })

        # --- 5. List WO Verifikasi ---
        verification_list_raw = WorkOrder.objects(status='pending_verification').order_by('created_at').limit(5)
        verification_list = []
        for wo in verification_list_raw:
            verification_list.append({
                "id": str(wo.id),
                "title": wo.title,
                "asset_name": wo.asset.name if wo.asset else "Unknown",
                "technician": wo.assigned_to.name if wo.assigned_to else "Unassigned",
                "completed_at": wo.completed_at.isoformat() if wo.completed_at else None
            })

        stats = {
            "total_assets": total_assets,
            "down_assets": down_assets,
            
            # Inventory Data (NEW)
            "total_components": total_components,
            "low_stock_components": low_stock_components,

            "open_work_orders": open_wo,
            "in_progress_work_orders": in_progress_wo,
            "pending_verification_orders": pending_verif_wo,
            "completed_work_orders": completed_wo,
            "total_work_orders": open_wo + in_progress_wo + pending_verif_wo + completed_wo,

            "upcoming_schedules": upcoming_schedules,
            "verification_needed_list": verification_list,
            
            # Predictive Maintenance Notifications (NEW)
            "predictive_maintenance_notifications": get_predictive_maintenance_notifications()
        }
        
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
