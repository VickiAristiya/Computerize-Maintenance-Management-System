from app import create_app
from app.models import User, ComponentItem, AssetTemplate, Asset, WorkOrder, MaintenanceSchedule, ComplianceLog
import datetime

app = create_app()


def safe_save(model, defaults, **filters):
    obj = model.objects(**filters).first()
    if obj:
        return obj
    return model(**{**filters, **defaults}).save()


def create_dummy_data():
    with app.app_context():
        # Users
        admin = User.objects(email='admin@cmms.com').first()
        if not admin:
            admin = User(name='Admin Utama', email='admin@cmms.com', role='admin')
        admin.set_password('password123')
        admin.save()

        manager = User.objects(email='manager@cmms.com').first()
        if not manager:
            manager = User(name='Manager Operasional', email='manager@cmms.com', role='manager')
        manager.set_password('password123')
        manager.save()

        technician = User.objects(email='tech@cmms.com').first()
        if not technician:
            technician = User(name='Teknisi Lapangan', email='tech@cmms.com', role='technician')
        technician.set_password('password123')
        technician.save()

        # Inventory components
        components_data = [
            {'name': 'Hydraulic Pump', 'part_number': 'HP-1001', 'stock_quantity': 8, 'location': 'Gudang Utama'},
            {'name': 'Filter Cartridge', 'part_number': 'FC-4300', 'stock_quantity': 3, 'location': 'Gudang Utama'},
            {'name': 'Belt Drive', 'part_number': 'BD-2204', 'stock_quantity': 15, 'location': 'Gudang Cabang'},
            {'name': 'Lubricant Oil', 'part_number': 'LO-2122', 'stock_quantity': 25, 'location': 'Gudang Utama'},
            {'name': 'Sensor Module', 'part_number': 'SM-9800', 'stock_quantity': 2, 'location': 'Gudang Sisi'},
            {'name': 'Bearing Set', 'part_number': 'BS-5567', 'stock_quantity': 5, 'location': 'Gudang Utama'},
            {'name': 'Fan Blades', 'part_number': 'FB-3302', 'stock_quantity': 12, 'location': 'Gudang Cabang'},
            {'name': 'Pressure Valve', 'part_number': 'PV-7711', 'stock_quantity': 4, 'location': 'Gudang Utama'},
        ]
        components = []
        for item in components_data:
            comp = safe_save(ComponentItem, {
                'part_number': item['part_number'],
                'stock_quantity': item['stock_quantity'],
                'location': item['location']
            }, name=item['name'])
            components.append(comp)

        # Asset templates
        press_template = safe_save(AssetTemplate, {
            'components': [components[0], components[1], components[3]]
        }, name='Press Machine')

        cnc_template = safe_save(AssetTemplate, {
            'components': [components[4], components[5], components[7]]
        }, name='CNC Milling Machine')

        conveyor_template = safe_save(AssetTemplate, {
            'components': [components[2], components[3], components[6]]
        }, name='Packaging Conveyor')

        # Assets
        press_asset = safe_save(Asset, {
            'machine_id': 'PR-001',
            'location': 'Line Produksi A',
            'status': 'running',
            'components': [components[0], components[1], components[3]]
        }, name='Press Mesin A1')

        cnc_asset = safe_save(Asset, {
            'machine_id': 'CNC-002',
            'location': 'Workshop B',
            'status': 'down',
            'components': [components[4], components[5], components[7]]
        }, name='CNC Milling B2')

        conveyor_asset = safe_save(Asset, {
            'machine_id': 'CV-003',
            'location': 'Line Packing C',
            'status': 'running',
            'components': [components[2], components[3], components[6]]
        }, name='Conveyor C3')

        # Work orders
        now = datetime.datetime.utcnow()
        work_orders_data = [
            {
                'title': 'Perbaikan kebocoran oli hidrolik',
                'description': 'Periksa dan ganti seal pada hydraulic pump.',
                'status': 'open',
                'priority': 'high',
                'type': 'repair',
                'component': components[0],
                'asset': press_asset,
                'assigned_to': technician,
                'created_by_role': 'manager',
                'created_at': now - datetime.timedelta(days=1),
                'due_date': now + datetime.timedelta(days=2),
            },
            {
                'title': 'Penggantian sensor modul suhu',
                'description': 'Sensor modul suhu menunjukkan pembacaan tidak stabil.',
                'status': 'in_progress',
                'priority': 'medium',
                'type': 'repair',
                'component': components[4],
                'asset': cnc_asset,
                'assigned_to': technician,
                'created_by_role': 'manager',
                'created_at': now - datetime.timedelta(days=3),
                'due_date': now + datetime.timedelta(days=1),
            },
            {
                'title': 'Verifikasi perbaikan belt conveyor',
                'description': 'Periksa hasil penggantian belt drive pada conveyor.',
                'status': 'pending_verification',
                'priority': 'high',
                'type': 'inspection',
                'component': components[2],
                'asset': conveyor_asset,
                'assigned_to': technician,
                'created_by_role': 'admin',
                'created_at': now - datetime.timedelta(days=5),
                'due_date': now - datetime.timedelta(days=1),
                'completed_at': now - datetime.timedelta(days=1),
            },
            {
                'title': 'Pengecekan preventif motor',
                'description': 'Pemeriksaan rutin motor press untuk mencegah kerusakan.',
                'status': 'completed',
                'priority': 'low',
                'type': 'preventive',
                'component': components[5],
                'asset': press_asset,
                'assigned_to': technician,
                'created_by_role': 'admin',
                'created_at': now - datetime.timedelta(days=10),
                'due_date': now - datetime.timedelta(days=2),
                'completed_at': now - datetime.timedelta(days=2),
            },
        ]
        work_orders = []
        for item in work_orders_data:
            wo = WorkOrder.objects(title=item['title']).first()
            if not wo:
                wo = WorkOrder(
                    title=item['title'],
                    description=item['description'],
                    status=item['status'],
                    priority=item['priority'],
                    type=item['type'],
                    component=item['component'],
                    asset=item['asset'],
                    assigned_to=item['assigned_to'],
                    created_by_role=item['created_by_role'],
                    created_at=item['created_at'],
                    due_date=item['due_date'],
                    completed_at=item.get('completed_at'),
                ).save()
            work_orders.append(wo)

        # Assign maintenance history to asset
        press_asset.maintenance_history = [wo for wo in work_orders if wo.asset == press_asset]
        press_asset.save()
        cnc_asset.maintenance_history = [wo for wo in work_orders if wo.asset == cnc_asset]
        cnc_asset.save()
        conveyor_asset.maintenance_history = [wo for wo in work_orders if wo.asset == conveyor_asset]
        conveyor_asset.save()

        # Maintenance schedules
        schedule_data = [
            {
                'asset': press_asset,
                'task_name': 'Ganti oli hidrolik',
                'frequency': 'monthly',
                'frequency_days': 30,
                'next_due_date': now + datetime.timedelta(days=3),
                'description_template': 'Ganti oli hidrolik dan periksa kebocoran.',
                'component': 'Lubricant Oil'
            },
            {
                'asset': cnc_asset,
                'task_name': 'Kalibrasi sensor temperatur',
                'frequency': 'bi-weekly',
                'frequency_days': 14,
                'next_due_date': now + datetime.timedelta(days=6),
                'description_template': 'Kalibrasi ulang semua sensor suhu.',
                'component': 'Sensor Module'
            },
            {
                'asset': conveyor_asset,
                'task_name': 'Periksa belt conveyor',
                'frequency': 'weekly',
                'frequency_days': 7,
                'next_due_date': now + datetime.timedelta(days=2),
                'description_template': 'Periksa kondisi belt dan pengencangan.',
                'component': 'Belt Drive'
            },
        ]
        for item in schedule_data:
            MaintenanceSchedule.objects(task_name=item['task_name'], asset=item['asset']).first() or MaintenanceSchedule(
                asset=item['asset'],
                task_name=item['task_name'],
                frequency=item['frequency'],
                frequency_days=item['frequency_days'],
                next_due_date=item['next_due_date'],
                description_template=item['description_template'],
                component=item['component']
            ).save()

        # Compliance logs
        compliance_data = [
            {
                'asset': press_asset,
                'regulation_name': 'ISO 9001 Audit',
                'status': 'pending',
                'next_check_due': now + datetime.timedelta(days=5),
                'evidence_document_url': 'https://example.com/evidence/iso9001-press'
            },
            {
                'asset': cnc_asset,
                'regulation_name': 'Inspection K3',
                'status': 'completed',
                'next_check_due': now + datetime.timedelta(days=12),
                'evidence_document_url': 'https://example.com/evidence/k3-cnc'
            },
            {
                'asset': conveyor_asset,
                'regulation_name': 'Pemeriksaan Lingkungan',
                'status': 'pending',
                'next_check_due': now + datetime.timedelta(days=8),
                'evidence_document_url': 'https://example.com/evidence/env-conveyor'
            },
        ]
        for item in compliance_data:
            ComplianceLog.objects(regulation_name=item['regulation_name'], asset=item['asset']).first() or ComplianceLog(
                asset=item['asset'],
                regulation_name=item['regulation_name'],
                status=item['status'],
                next_check_due=item['next_check_due'],
                evidence_document_url=item['evidence_document_url']
            ).save()

        print('Seed dummy data selesai. Database sekarang berisi aset, komponen, template, WO, jadwal, compliance, dan users.')


if __name__ == '__main__':
    create_dummy_data()
