# /cmms-backend/app/__init__.py
from flask import Flask
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from flask_bcrypt import Bcrypt 
import os

# Inisialisasi Database
db = MongoEngine()
bcrypt = Bcrypt() 

def create_app():
    app = Flask(__name__)
    
    # --- KONFIGURASI KONEKSI MONGODB LOKAL ---
    DB_USERNAME = "vicki"
    DB_PASSWORD = "123456"
    DB_NAME = "cmms_db"      
    AUTH_DB = "admin"        
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_insecure_key_anda_harus_menggantinya')
    
    app.config['MONGODB_SETTINGS'] = {
        'db': DB_NAME,
        'host': f'mongodb://{DB_USERNAME}:{DB_PASSWORD}@localhost:27017/{DB_NAME}?authSource={AUTH_DB}'
    }
    
    # Inisialisasi DB dan Bcrypt dengan aplikasi Flask
    db.init_app(app)
    bcrypt.init_app(app) 
    
    # Izinkan CORS
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})

    # Daftarkan blueprint (rute) Anda
    
    from .api.asset_routes import assets_bp
    app.register_blueprint(assets_bp, url_prefix='/api')
    
    from .api.wo_routes import wo_bp
    app.register_blueprint(wo_bp, url_prefix='/api')
    
    from .api.schedule_routes import schedule_bp
    app.register_blueprint(schedule_bp, url_prefix='/api')
    
    from .api.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    # --- PERBAIKAN FOKUS DI SINI ---
    from .api.compliance_routes import compliance_bp
    # Pastikan prefix adalah '/api/compliance' agar '/stats' menjadi /api/compliance/stats
    app.register_blueprint(compliance_bp, url_prefix='/api/compliance')
    # ------------------------------
    
    from .api.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/api')
    
    from .api.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .api.inventory_routes import inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')

    from .api.template_routes import template_bp
    app.register_blueprint(template_bp, url_prefix='/api')

    from .api.ml_routes import ml_bp
    app.register_blueprint(ml_bp, url_prefix='/api/ml')

    return app