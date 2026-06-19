# /cmms-backend/app/models.py
from . import db, bcrypt
import datetime

# --- Sub-dokumen untuk Komponen ---
class Component(db.EmbeddedDocument):
    name = db.StringField(required=True)
    part_number = db.StringField()
    last_checked = db.DateTimeField()

# --- Model Inventaris Gudang ---
class ComponentItem(db.Document):
    name = db.StringField(required=True, unique=True)
    part_number = db.StringField()
    stock_quantity = db.IntField(default=0)
    location = db.StringField(default='Gudang Utama')

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "part_number": self.part_number,
            "stock_quantity": self.stock_quantity,
            "location": self.location
        }

# --- Model Utama Aset (Mesin) ---
class Asset(db.Document):
    name = db.StringField(required=True)
    machine_id = db.StringField(unique=True, required=True)
    location = db.StringField()
    status = db.StringField(default='running')
    
    # --- FIELD BARU: Gambar Aset ---
    image = db.StringField() # Base64 string
    # -----------------------------

    components = db.ListField(db.ReferenceField(ComponentItem))
    maintenance_history = db.ListField(db.ReferenceField('WorkOrder'))
    
    def to_json(self):
        component_list = []
        for comp in self.components:
            if comp: 
                component_list.append({
                    "id": str(comp.id),
                    "name": comp.name,
                    "stock_quantity": comp.stock_quantity
                })
        return {
            "id": str(self.id),
            "name": self.name,
            "machine_id": self.machine_id,
            "location": self.location,
            "status": self.status,
            "image": self.image, 
            "components": component_list 
        }

# --- Model User ---
class User(db.Document):
    name = db.StringField(required=True)
    email = db.StringField(unique=True, required=True)
    password = db.StringField(required=True) 
    role = db.StringField(default='technician')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "role": self.role
        }

# --- Model Work Order ---
class WorkOrder(db.Document):
    title = db.StringField(required=True)
    description = db.StringField()
    
    # Status flow: pending_approval -> open -> in_progress -> pending_verification -> completed
    status = db.StringField(default='open') 
    
    priority = db.StringField(default='medium')
    type = db.StringField()
    component = db.ReferenceField(ComponentItem) 
    asset = db.ReferenceField(Asset, required=True)
    assigned_to = db.ReferenceField(User)
    
    # Role pembuat (admin/manager)
    created_by_role = db.StringField() 
    
    # Foto saat pembuatan (Masalah/Pencegahan)
    initial_image = db.StringField() 
    
    # Foto saat selesai (Bukti Perbaikan)
    evidence_image = db.StringField() 
    
    created_at = db.DateTimeField(default=datetime.datetime.utcnow)
    due_date = db.DateTimeField()
    completed_at = db.DateTimeField()

    def to_json(self):
        user_name = self.assigned_to.name if self.assigned_to else ""
        asset_name = self.asset.name if self.asset else "Aset Tidak Ditemukan"
        asset_id = str(self.asset.id) if self.asset else None
        component_name = self.component.name if self.component else ""
        component_id = str(self.component.id) if self.component else None
        
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "type": self.type,
            "component_id": component_id,
            "component_name": component_name,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "assigned_to": user_name,
            "created_by_role": self.created_by_role,
            "initial_image": self.initial_image,
            "evidence_image": self.evidence_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

# --- Model Maintenance Schedule ---
class MaintenanceSchedule(db.Document):
    asset = db.ReferenceField(Asset, required=True)
    task_name = db.StringField()
    frequency = db.StringField()
    frequency_days = db.IntField()
    next_due_date = db.DateTimeField()
    description_template = db.StringField()
    component = db.StringField() 

    def to_json(self):
        asset_name = self.asset.name if self.asset else "Aset Tidak Ditemukan"
        return {
            "id": str(self.id),
            "asset_id": str(self.asset.id),
            "asset_name": asset_name,
            "task_name": self.task_name,
            "frequency": self.frequency,
            "frequency_days": self.frequency_days,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "description_template": self.description_template,
            "component": self.component
        }

# --- Model Compliance Log ---
class ComplianceLog(db.Document):
    asset = db.ReferenceField(Asset, required=True)
    regulation_name = db.StringField()
    status = db.StringField(default='pending')
    next_check_due = db.DateTimeField()
    evidence_document_url = db.StringField()
    
    def to_json(self):
        asset_name = self.asset.name if self.asset else "Aset Tidak Ditemukan"
        return {
            "id": str(self.id),
            "asset_id": str(self.asset.id),
            "asset_name": asset_name,
            "regulation_name": self.regulation_name,
            "status": self.status,
            "next_check_due": self.next_check_due.isoformat() if self.next_check_due else None,
            "evidence_document_url": self.evidence_document_url,
        }

# --- Model Template Aset ---
class AssetTemplate(db.Document):
    name = db.StringField(required=True, unique=True)
    components = db.ListField(db.ReferenceField(ComponentItem))

    def to_json(self):
        component_ids = [str(comp.id) for comp in self.components if comp]
        return {
            "id": str(self.id),
            "name": self.name,
            "component_ids": component_ids
        }

# --- Model Data Sensor untuk Predictive Maintenance ---
class SensorData(db.Document):
    asset = db.ReferenceField(Asset, required=True)
    timestamp = db.DateTimeField(default=datetime.datetime.utcnow)
    
    # Metrik sensor (sesuaikan dengan jenis mesin)
    temperature = db.FloatField()  # Suhu (°C)
    vibration = db.FloatField()    # Getaran (mm/s²)
    pressure = db.FloatField()     # Tekanan (bar)
    current = db.FloatField()      # Arus (A)
    voltage = db.FloatField()      # Tegangan (V)
    rpm = db.FloatField()          # Putaran per menit

    # Fitur sensor khusus model compressor bearing
    motor_power = db.FloatField()
    torque = db.FloatField()
    outlet_pressure_bar = db.FloatField()
    air_flow = db.FloatField()
    noise_db = db.FloatField()
    outlet_temp = db.FloatField()
    wpump_outlet_press = db.FloatField()
    water_inlet_temp = db.FloatField()
    water_outlet_temp = db.FloatField()
    wpump_power = db.FloatField()
    water_flow = db.FloatField()
    oilpump_power = db.FloatField()
    oil_tank_temp = db.FloatField()
    gaccx = db.FloatField()
    gaccy = db.FloatField()
    gaccz = db.FloatField()
    haccx = db.FloatField()
    haccy = db.FloatField()
    haccz = db.FloatField()

    # Metadata simulator untuk demo predictive maintenance
    demo_mode = db.StringField()
    demo_stage = db.StringField()
    demo_expected_risk = db.StringField()
    demo_expected_action = db.StringField()
    
    # Status kesehatan (0-1, dihitung oleh ML)
    health_score = db.FloatField(default=1.0)
    
    # Prediksi failure
    predicted_failure_days = db.FloatField()  # Hari sampai failure
    failure_probability = db.FloatField()     # Probabilitas failure (0-1)

    def to_json(self):
        return {
            "id": str(self.id),
            "asset_id": str(self.asset.id),
            "asset_name": self.asset.name,
            "timestamp": self.timestamp.isoformat(),
            "temperature": self.temperature,
            "vibration": self.vibration,
            "pressure": self.pressure,
            "current": self.current,
            "voltage": self.voltage,
            "rpm": self.rpm,
            "motor_power": self.motor_power,
            "torque": self.torque,
            "outlet_pressure_bar": self.outlet_pressure_bar,
            "air_flow": self.air_flow,
            "noise_db": self.noise_db,
            "outlet_temp": self.outlet_temp,
            "wpump_outlet_press": self.wpump_outlet_press,
            "water_inlet_temp": self.water_inlet_temp,
            "water_outlet_temp": self.water_outlet_temp,
            "wpump_power": self.wpump_power,
            "water_flow": self.water_flow,
            "oilpump_power": self.oilpump_power,
            "oil_tank_temp": self.oil_tank_temp,
            "gaccx": self.gaccx,
            "gaccy": self.gaccy,
            "gaccz": self.gaccz,
            "haccx": self.haccx,
            "haccy": self.haccy,
            "haccz": self.haccz,
            "demo_mode": self.demo_mode,
            "demo_stage": self.demo_stage,
            "demo_expected_risk": self.demo_expected_risk,
            "demo_expected_action": self.demo_expected_action,
            "health_score": self.health_score,
            "predicted_failure_days": self.predicted_failure_days,
            "failure_probability": self.failure_probability
        }
