"""
Temporary script: inject varied completed work orders for Riwayat Perawatan demo.
Run: python seed_history.py
"""
import base64
import datetime
from app import create_app
from app.models import Asset, ComponentItem, User, WorkOrder

app = create_app()


# ---------------------------------------------------------------------------
# Tiny SVG placeholder images (encoded as data URIs) so the history page
# shows something in the photo gallery without needing real files.
# ---------------------------------------------------------------------------

def _svg_b64(bg: str, label: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200">'
        f'<rect width="320" height="200" rx="8" fill="{bg}"/>'
        f'<text x="160" y="95" text-anchor="middle" font-family="Arial" '
        f'font-size="15" font-weight="bold" fill="#fff">{label}</text>'
        f'<text x="160" y="118" text-anchor="middle" font-family="Arial" '
        f'font-size="11" fill="#ffffffcc">Foto Placeholder</text>'
        f'</svg>'
    )
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


IMG_BEFORE = _svg_b64("#dc2626", "Kondisi Awal / Masalah")
IMG_AFTER  = _svg_b64("#16a34a", "Kondisi Selesai / Bukti")

# Beberapa variasi warna untuk gambar "before" agar lebih bervariasi
IMG_BEFORE_ORANGE = _svg_b64("#ea580c", "Kondisi Awal / Rusak")
IMG_BEFORE_AMBER  = _svg_b64("#d97706", "Kondisi Awal / Aus")
IMG_AFTER_TEAL    = _svg_b64("#0d9488", "Kondisi Selesai / Bersih")
IMG_AFTER_BLUE    = _svg_b64("#2563eb", "Kondisi Selesai / Terpasang")


# ---------------------------------------------------------------------------
# Work order definitions
# ---------------------------------------------------------------------------

def wo_entries(induksi, forging, robot, motor_ac, compressor, tech, admin_user, manager_user, comp_map):
    """
    Return list of dicts for completed WOs.
    comp_map: dict name -> ComponentItem, contoh key:
      'Kumparan Induksi', 'Capacitor Bank', 'Pompa Air Pendingin',
      'Die Set Forging', 'Hydraulic Cylinder', 'Guide Bushing',
      'Servo Motor', 'Encoder Module', 'Robot Gripper',
      'Winding Motor AC', 'Bearing Motor', 'Fan Blade Pendingin',
      'Air Filter Compressor', 'Bearing Set Compressor'
    """
    now = datetime.datetime.utcnow()
    d = lambda days: now - datetime.timedelta(days=days)
    c = comp_map.get

    return [
        # ---- Preventive: Mesin Induksi ----
        {
            "title": "Megger test isolasi kumparan induksi rutin",
            "description": (
                "Pengujian tahanan isolasi (megger test) rutin bulanan pada kumparan induksi. "
                "Hasil tahanan isolasi 85 MΩ, masih dalam batas aman di atas 50 MΩ."
            ),
            "type": "preventive", "priority": "low",
            "asset": induksi, "component": c("Kumparan Induksi"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(90), "due_date": d(85), "completed_at": d(86),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Pemeriksaan dan pembersihan capacitor bank",
            "description": (
                "Pemeriksaan kapasitansi capacitor bank untuk kompensasi daya reaktif. "
                "Ditemukan debu tebal pada terminal, dibersihkan dan nilai kapasitansi "
                "diverifikasi masih sesuai spesifikasi 50 kVAR."
            ),
            "type": "preventive", "priority": "medium",
            "asset": induksi, "component": c("Capacitor Bank"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(65), "due_date": d(60), "completed_at": d(61),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Perawatan sistem pendingin air kumparan induksi",
            "description": (
                "Pemeriksaan sirkulasi air pendingin kumparan sesuai interval 500 jam operasional. "
                "Ditemukan penyumbatan ringan pada saringan pompa, dibersihkan hingga aliran normal."
            ),
            "type": "preventive", "priority": "low",
            "asset": induksi, "component": c("Pompa Air Pendingin"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(30), "due_date": d(28), "completed_at": d(28),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },

        # ---- Corrective: Mesin Induksi ----
        {
            "title": "Perbaikan isolasi kumparan induksi menggelembung",
            "description": (
                "Ditemukan isolasi kumparan menggelembung akibat panas berlebih saat proses "
                "peleburan berkepanjangan. Lapisan isolasi diganti dan diuji ulang, tahanan "
                "isolasi kembali normal dari 12 MΩ menjadi 90 MΩ."
            ),
            "type": "corrective", "priority": "high",
            "asset": induksi, "component": c("Kumparan Induksi"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(75), "due_date": d(73), "completed_at": d(74),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Penggantian capacitor bank rusak",
            "description": (
                "Salah satu unit capacitor bank mengalami penurunan kapasitansi drastis "
                "menyebabkan power factor turun ke 0,78. Unit diganti dan power factor "
                "kembali ke 0,96."
            ),
            "type": "corrective", "priority": "high",
            "asset": induksi, "component": c("Capacitor Bank"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(20), "due_date": d(18), "completed_at": d(19),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Preventive: Mesin Forging ----
        {
            "title": "Inspeksi keausan permukaan die set forging",
            "description": (
                "Inspeksi periodik permukaan die set untuk mendeteksi keausan dan retak rambut "
                "akibat beban impact repetitif. Deviasi dimensi 0,2mm masih dalam toleransi."
            ),
            "type": "preventive", "priority": "medium",
            "asset": forging, "component": c("Die Set Forging"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(80), "due_date": d(76), "completed_at": d(77),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Penggantian guide bushing preventif",
            "description": (
                "Guide bushing sudah mencapai 2000 siklus tempa. Penggantian preventif dilakukan "
                "sebelum menyebabkan misalignment pada proses forging. Bushing baru terpasang presisi."
            ),
            "type": "preventive", "priority": "medium",
            "asset": forging, "component": c("Guide Bushing"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(55), "due_date": d(50), "completed_at": d(51),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Pemeriksaan dan pengisian oli hydraulic cylinder",
            "description": (
                "Pemeriksaan rutin tekanan kerja hydraulic cylinder dan pengisian oli sesuai "
                "jadwal 250 jam. Tekanan kerja terverifikasi stabil di 210 bar."
            ),
            "type": "preventive", "priority": "low",
            "asset": forging, "component": c("Hydraulic Cylinder"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(40), "due_date": d(37), "completed_at": d(38),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Corrective: Mesin Forging ----
        {
            "title": "Perbaikan kebocoran seal hydraulic cylinder",
            "description": (
                "Ditemukan kebocoran oli pada seal hydraulic cylinder utama saat proses penempaan. "
                "Seal kit diganti, tekanan kerja dikembalikan ke 210 bar tanpa kebocoran."
            ),
            "type": "corrective", "priority": "high",
            "asset": forging, "component": c("Hydraulic Cylinder"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(70), "due_date": d(68), "completed_at": d(69),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Penggantian die set retak akibat beban lebih",
            "description": (
                "Die set forging mengalami retak akibat beban impact melebihi kapasitas nominal. "
                "Unit diganti dengan die set baru dan parameter tekanan hammer disesuaikan."
            ),
            "type": "corrective", "priority": "high",
            "asset": forging, "component": c("Die Set Forging"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(45), "due_date": d(43), "completed_at": d(44),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Perbaikan guide bushing aus menyebabkan misalignment",
            "description": (
                "Guide bushing aus menyebabkan hasil tempa tidak center hingga deviasi 1,5mm. "
                "Bushing diganti dan alignment mekanis dikalibrasi ulang."
            ),
            "type": "corrective", "priority": "medium",
            "asset": forging, "component": c("Guide Bushing"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(15), "due_date": d(13), "completed_at": d(14),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Preventive: Robot ----
        {
            "title": "Kalibrasi ulang TCP (Tool Center Point) robot",
            "description": (
                "Kalibrasi rutin mingguan Tool Center Point robot welding R3. "
                "Deviasi posisi terverifikasi 0,1mm, masih dalam toleransi presisi las."
            ),
            "type": "preventive", "priority": "low",
            "asset": robot, "component": c("Servo Motor"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(85), "due_date": d(82), "completed_at": d(82),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Pemeriksaan dan pelumasan gripper robot",
            "description": (
                "Pemeriksaan mekanisme gripper untuk memastikan cengkeraman tetap kuat. "
                "Pelumasan pada joint gripper dilakukan, gaya cengkeram terukur 450N sesuai spesifikasi."
            ),
            "type": "preventive", "priority": "medium",
            "asset": robot, "component": c("Robot Gripper"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(50), "due_date": d(47), "completed_at": d(48),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_TEAL,
        },
        {
            "title": "Update firmware dan kalibrasi encoder robot",
            "description": (
                "Update firmware controller robot dan kalibrasi ulang encoder pada seluruh sumbu "
                "sesuai jadwal 1000 jam operasional. Semua sumbu bergerak sesuai referensi standar."
            ),
            "type": "preventive", "priority": "low",
            "asset": robot, "component": c("Encoder Module"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(25), "due_date": d(23), "completed_at": d(23),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },

        # ---- Corrective: Robot ----
        {
            "title": "Penggantian encoder robot akibat drift posisi",
            "description": (
                "Encoder module pada sumbu 4 mengalami drift posisi 0,8mm menyebabkan hasil las "
                "tidak presisi. Modul diganti dan kalibrasi TCP diulang, hasil las kembali presisi."
            ),
            "type": "corrective", "priority": "high",
            "asset": robot, "component": c("Encoder Module"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(60), "due_date": d(59), "completed_at": d(59),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Perbaikan gripper robot gagal mencengkeram",
            "description": (
                "Gripper gagal mencengkeram material akibat pegas mekanisme melemah. "
                "Set pegas dan bantalan gripper diganti, gaya cengkeram kembali normal."
            ),
            "type": "corrective", "priority": "medium",
            "asset": robot, "component": c("Robot Gripper"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(35), "due_date": d(33), "completed_at": d(34),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Perbaikan servo motor overheat sumbu 2",
            "description": (
                "Servo motor sumbu 2 mengalami overheat berulang saat gerakan berkecepatan tinggi. "
                "Pemeriksaan menemukan kipas pendingin motor tersumbat debu. Setelah dibersihkan, "
                "suhu motor turun 18°C ke level normal."
            ),
            "type": "corrective", "priority": "high",
            "asset": robot, "component": c("Servo Motor"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(10), "due_date": d(9), "completed_at": d(9),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Extra: Motor AC & Compressor, mixed priorities / recent ----
        {
            "title": "Inspeksi menyeluruh Mesin Induksi pasca overhaul",
            "description": (
                "Inspeksi komprehensif setelah overhaul besar Mesin Induksi I1. Sistem elektrik, "
                "pendingin, dan mekanik diperiksa. Hasil: semua sistem dalam kondisi baik, mesin "
                "siap beroperasi kembali dengan kapasitas penuh."
            ),
            "type": "preventive", "priority": "high",
            "asset": induksi, "component": None,
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(100), "due_date": d(96), "completed_at": d(97),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Penggantian winding motor AC akibat isolasi breakdown",
            "description": (
                "Winding motor AC blower M4 mengalami isolasi breakdown menyebabkan trip proteksi "
                "berulang. Rewinding dilakukan dan tahanan isolasi diuji kembali normal di atas 100 MΩ."
            ),
            "type": "corrective", "priority": "high",
            "asset": motor_ac, "component": c("Winding Motor AC"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(5), "due_date": d(4), "completed_at": d(4),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Penggantian bearing motor AC bersuara kasar",
            "description": (
                "Bearing motor AC blower mengeluarkan suara grinding pada RPM operasional. "
                "Bearing diganti dan getaran motor kembali ke level normal (< 2 mm/s)."
            ),
            "type": "corrective", "priority": "medium",
            "asset": motor_ac, "component": c("Bearing Motor"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(18), "due_date": d(16), "completed_at": d(17),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_TEAL,
        },
        {
            "title": "Pembersihan fan blade pendingin motor AC",
            "description": (
                "Fan blade pendingin motor AC dibersihkan dari akumulasi debu setebal 6mm yang "
                "menyebabkan suhu motor naik. Setelah dibersihkan, suhu motor turun 10°C."
            ),
            "type": "preventive", "priority": "low",
            "asset": motor_ac, "component": c("Fan Blade Pendingin"),
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(42), "due_date": d(39), "completed_at": d(40),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Penggantian air filter compressor tersumbat",
            "description": (
                "Air filter compressor tersumbat kotoran menyebabkan aliran udara turun di bawah "
                "spesifikasi. Filter diganti, air flow kembali normal di rentang 500-700 m³/h."
            ),
            "type": "preventive", "priority": "medium",
            "asset": compressor, "component": c("Air Filter Compressor"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(28), "due_date": d(26), "completed_at": d(26),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Pemeriksaan bearing compressor setelah alarm getaran & noise",
            "description": (
                "Sistem monitoring ML mendeteksi peningkatan noise dan getaran pada bearing "
                "compressor. Inspeksi menemukan bearing kurang pelumas, dilakukan pelumasan dan "
                "alarm tidak muncul kembali setelah 24 jam."
            ),
            "type": "corrective", "priority": "medium",
            "asset": compressor, "component": c("Bearing Set Compressor"),
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(3), "due_date": d(2), "completed_at": d(2),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_TEAL,
        },
    ]


def seed():
    with app.app_context():
        induksi    = Asset.objects(machine_id='IND-001').first()
        forging    = Asset.objects(machine_id='FRG-002').first()
        robot      = Asset.objects(machine_id='ROB-003').first()
        motor_ac   = Asset.objects(machine_id='MTR-004').first()
        compressor = Asset.objects(machine_id='CMP-DUMMY-001').first()
        tech       = User.objects(email='tech@cmms.com').first()
        manager    = User.objects(email='manager@cmms.com').first()
        admin_u    = User.objects(email='admin@cmms.com').first()
        comps      = list(ComponentItem.objects())

        if not all([induksi, forging, robot, motor_ac, compressor, tech]):
            print("ERROR: Jalankan seed_data.py terlebih dahulu untuk membuat aset dan user dasar.")
            return

        comp_map = {c.name: c for c in comps}

        entries = wo_entries(induksi, forging, robot, motor_ac, compressor, tech, admin_u, manager, comp_map)

        created = 0
        skipped = 0
        for entry in entries:
            if WorkOrder.objects(title=entry['title']).first():
                skipped += 1
                continue

            wo = WorkOrder(
                title=entry['title'],
                description=entry['description'],
                status='completed',
                type=entry['type'],
                priority=entry['priority'],
                asset=entry['asset'],
                component=entry.get('component'),
                assigned_to=entry['assigned_to'],
                created_by_role=entry['created_by_role'],
                initial_image=entry['initial_image'],
                evidence_image=entry['evidence_image'],
                created_at=entry['created_at'],
                due_date=entry['due_date'],
                completed_at=entry['completed_at'],
            )
            wo.save()
            created += 1

        print(f"Selesai: {created} WO baru dibuat, {skipped} sudah ada (dilewati).")
        print(f"Total riwayat perawatan: {WorkOrder.objects(status='completed').count()} entri.")


if __name__ == '__main__':
    seed()
