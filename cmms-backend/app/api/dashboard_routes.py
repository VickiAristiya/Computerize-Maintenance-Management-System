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

COMPONENT_LABELS = {
    "bearings": "Bearing",
    "wpump": "Water Pump",
    "radiator": "Radiator",
    "exvalve": "Exhaust Valve",
}

PRIORITY_ORDER = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'very_low': 0}


def get_predictive_maintenance_notifications():
    """Notifikasi predictive maintenance untuk semua 4 komponen per asset."""
    notifications = []

    if not predictor.is_ready():
        return notifications

    try:
        assets = Asset.objects()

        for asset in assets:
            latest_sensor = SensorData.objects(asset=asset).order_by('-timestamp').first()
            if not latest_sensor:
                continue

            prediction = predictor.predict(_sensor_to_payload(latest_sensor))
            if not prediction.get("ok"):
                continue

            components = prediction.get("components", {})

            # Kumpulkan komponen yang bermasalah (fault_prob > 0.3)
            faulty = []
            worst_priority = 0
            worst_risk = "very_low"

            for comp_key, comp_data in components.items():
                fault_prob = comp_data.get("failure_probability", 0)
                risk_level = comp_data.get("risk_level", "very_low")
                priority = comp_data.get("priority", "low")

                if fault_prob > 0.3:
                    faulty.append({
                        "key": comp_key,
                        "label": COMPONENT_LABELS.get(comp_key, comp_key),
                        "prediction": comp_data.get("prediction"),
                        "status": comp_data.get("status"),
                        "risk_level": risk_level,
                        "failure_probability": fault_prob,
                        "health_score": comp_data.get("health_score"),
                        "predicted_days": comp_data.get("predicted_days"),
                        "due_date": comp_data.get("due_date"),
                    })
                    if PRIORITY_ORDER.get(priority, 0) > worst_priority:
                        worst_priority = PRIORITY_ORDER.get(priority, 0)
                        worst_risk = risk_level

            if not faulty:
                continue

            worst_priority_label = {4: 'critical', 3: 'high', 2: 'medium', 1: 'low'}.get(worst_priority, 'low')

            notifications.append({
                "id": f"pred-{str(asset.id)}",
                "asset_id": str(asset.id),
                "machine_id": asset.machine_id,
                "asset_name": asset.name,
                "type": "predictive_maintenance",
                "title": "Prediksi Maintenance Diperlukan",
                "message": prediction.get("recommendation", ""),
                "priority": worst_priority_label,
                "risk_level": worst_risk,
                "overall_health_score": prediction.get("overall_health_score"),
                "recommendation": prediction.get("recommendation", ""),
                "faulty_components": faulty,
                "due_date": prediction.get("due_date"),
                "predicted_days": prediction.get("predicted_days"),
                "failure_probability": prediction.get("failure_probability"),
                "health_score": prediction.get("health_score"),
                "link": "/work-orders",
            })

        notifications.sort(
            key=lambda x: (PRIORITY_ORDER.get(x['priority'], 0), x['failure_probability'] or 0),
            reverse=True,
        )
        return notifications[:10]

    except Exception as e:
        print(f"Error getting predictive notifications: {e}")
        return notifications

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        # --- 1. Statistik Aset ---
        total_assets = Asset.objects.count()
        down_assets = Asset.objects(status__in=['down', 'breakdown']).count()
        
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
