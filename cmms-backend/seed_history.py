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

def wo_entries(press, cnc, conveyor, tech, admin_user, manager_user, comps):
    """
    Return list of dicts for completed WOs.
    comps index:
      0=Hydraulic Pump, 1=Filter Cartridge, 2=Belt Drive,
      3=Lubricant Oil,  4=Sensor Module,    5=Bearing Set,
      6=Fan Blades,     7=Pressure Valve
    """
    now = datetime.datetime.utcnow()
    d = lambda days: now - datetime.timedelta(days=days)

    return [
        # ---- Preventive: Press ----
        {
            "title": "Penggantian filter oli hidrolik rutin",
            "description": (
                "Filter oli hidrolik pada Press Mesin A1 sudah mencapai batas jam operasi. "
                "Dilakukan penggantian filter sesuai jadwal preventif bulanan."
            ),
            "type": "preventive", "priority": "low",
            "asset": press, "component": comps[1],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(90), "due_date": d(85), "completed_at": d(86),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Pelumasan dan pengecekan pompa hidrolik",
            "description": (
                "Pemeriksaan tekanan kerja pompa hidrolik, pengecekan kebocoran seal, "
                "dan pelumasan pada fitting yang kering. Tekanan kerja normal di 180 bar."
            ),
            "type": "preventive", "priority": "medium",
            "asset": press, "component": comps[0],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(65), "due_date": d(60), "completed_at": d(61),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Penggantian oli mesin press berkala",
            "description": (
                "Penggantian pelumas mesin sesuai interval 500 jam operasional. "
                "Oli lama menunjukkan kontaminasi ringan. Oli baru Shell Tellus S2 M46 digunakan."
            ),
            "type": "preventive", "priority": "low",
            "asset": press, "component": comps[3],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(30), "due_date": d(28), "completed_at": d(28),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },

        # ---- Corrective: Press ----
        {
            "title": "Perbaikan kebocoran seal pompa hidrolik",
            "description": (
                "Ditemukan kebocoran oli pada seal pompa hidrolik kiri. "
                "Penggantian seal kit dilakukan, tekanan dikembalikan ke operasional normal. "
                "Konsumsi oli menurun dari 0,5L/hari menjadi 0."
            ),
            "type": "corrective", "priority": "high",
            "asset": press, "component": comps[0],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(75), "due_date": d(73), "completed_at": d(74),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Penggantian pressure valve bocor",
            "description": (
                "Pressure valve pada jalur utama mengalami kebocoran internal yang menyebabkan "
                "penurunan tekanan kerja dari 200 bar ke 160 bar. Valve diganti dengan unit baru."
            ),
            "type": "corrective", "priority": "high",
            "asset": press, "component": comps[7],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(20), "due_date": d(18), "completed_at": d(19),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Preventive: CNC ----
        {
            "title": "Kalibrasi sensor suhu spindle CNC",
            "description": (
                "Kalibrasi periodik sensor suhu pada spindle CNC Milling B2. "
                "Pembacaan suhu diverifikasi terhadap referensi terstandar, deviasi 0,3°C masih dalam toleransi."
            ),
            "type": "preventive", "priority": "medium",
            "asset": cnc, "component": comps[4],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(80), "due_date": d(76), "completed_at": d(77),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Penggantian bearing spindle CNC preventif",
            "description": (
                "Bearing spindle utama sudah mencapai 2000 jam operasional. "
                "Penggantian preventif dilakukan sebelum tanda keausan muncul. "
                "Bearing baru SKF 6205-2RS dipasang."
            ),
            "type": "preventive", "priority": "medium",
            "asset": cnc, "component": comps[5],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(55), "due_date": d(50), "completed_at": d(51),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Pemeriksaan dan pelumasan ball screw CNC",
            "description": (
                "Pelumasan rutin ball screw sumbu X, Y, dan Z sesuai jadwal 250 jam. "
                "Semua sumbu bergerak lancar, tidak ada backlash berlebih ditemukan."
            ),
            "type": "preventive", "priority": "low",
            "asset": cnc, "component": comps[3],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(40), "due_date": d(37), "completed_at": d(38),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Corrective: CNC ----
        {
            "title": "Penggantian sensor modul suhu rusak",
            "description": (
                "Sensor modul suhu pada sumbu Z menunjukkan pembacaan error E-04 (short circuit). "
                "Modul diganti dengan unit baru, sistem dikalibrasi ulang dan berfungsi normal."
            ),
            "type": "corrective", "priority": "high",
            "asset": cnc, "component": comps[4],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(70), "due_date": d(68), "completed_at": d(69),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Perbaikan bearing spindle aus akibat beban lebih",
            "description": (
                "Bearing spindle mengeluarkan suara abnormal (grinding noise) pada RPM di atas 3000. "
                "Pemeriksaan menunjukkan permukaan aus akibat overload. Bearing diganti dan "
                "parameter batas beban di-reset."
            ),
            "type": "corrective", "priority": "high",
            "asset": cnc, "component": comps[5],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(45), "due_date": d(43), "completed_at": d(44),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Perbaikan pressure valve CNC coolant system",
            "description": (
                "Sistem pendingin coolant tidak mengalir dengan baik karena pressure valve tersumbat. "
                "Valve dibersihkan dari kerak dan serpihan aluminium. Aliran coolant kembali normal."
            ),
            "type": "corrective", "priority": "medium",
            "asset": cnc, "component": comps[7],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(15), "due_date": d(13), "completed_at": d(14),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Preventive: Conveyor ----
        {
            "title": "Pemeriksaan dan penyetelan tegangan belt conveyor",
            "description": (
                "Pemeriksaan tegangan belt mingguan pada Conveyor C3. "
                "Belt kanan ditemukan kendur 5mm dari spesifikasi, dilakukan penyetelan idler. "
                "Tegangan setelah penyetelan: 120N sesuai standar."
            ),
            "type": "preventive", "priority": "low",
            "asset": conveyor, "component": comps[2],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(85), "due_date": d(82), "completed_at": d(82),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Pembersihan dan pelumasan fan blade conveyor",
            "description": (
                "Fan blade pada motor conveyor dibersihkan dari debu dan serpihan material. "
                "Ditemukan akumulasi debu setebal 8mm yang menyebabkan panas berlebih. "
                "Setelah pembersihan, suhu motor turun 12°C."
            ),
            "type": "preventive", "priority": "medium",
            "asset": conveyor, "component": comps[6],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(50), "due_date": d(47), "completed_at": d(48),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_TEAL,
        },
        {
            "title": "Penggantian oli gearbox conveyor",
            "description": (
                "Penggantian oli gearbox reduksi sesuai jadwal 1000 jam operasional. "
                "Analisis oli lama menunjukkan kontaminasi logam halus. "
                "Oli baru Mobil SHC 630 digunakan sesuai rekomendasi pabrikan."
            ),
            "type": "preventive", "priority": "low",
            "asset": conveyor, "component": comps[3],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(25), "due_date": d(23), "completed_at": d(23),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_BLUE,
        },

        # ---- Corrective: Conveyor ----
        {
            "title": "Penggantian belt conveyor putus di jalur C",
            "description": (
                "Belt conveyor putus pada sambungan ke-3 saat produksi berjalan. "
                "Mesin dihentikan darurat. Belt baru dengan panjang 12m dipasang, "
                "sambungan menggunakan mechanical splice untuk kecepatan recovery."
            ),
            "type": "corrective", "priority": "high",
            "asset": conveyor, "component": comps[2],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(60), "due_date": d(59), "completed_at": d(59),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Perbaikan fan blade conveyor retak",
            "description": (
                "Salah satu fan blade motor penggerak ditemukan retak akibat getaran berlebih. "
                "Seluruh set fan blade diganti untuk menjaga keseimbangan rotasi. "
                "Getaran motor kembali ke level normal (< 2 mm/s)."
            ),
            "type": "corrective", "priority": "medium",
            "asset": conveyor, "component": comps[6],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(35), "due_date": d(33), "completed_at": d(34),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Perbaikan sistem kontrol conveyor error E-12",
            "description": (
                "Sistem kontrol menampilkan error E-12 (overload protection) berulang kali. "
                "Pemeriksaan menemukan short circuit pada kabel sensor beban. "
                "Kabel diganti dan parameter kontrol dikalibrasi ulang."
            ),
            "type": "corrective", "priority": "high",
            "asset": conveyor, "component": comps[4],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(10), "due_date": d(9), "completed_at": d(9),
            "initial_image": IMG_BEFORE_ORANGE, "evidence_image": IMG_AFTER_TEAL,
        },

        # ---- Extra: mixed priorities / recent ----
        {
            "title": "Inspeksi menyeluruh Press Mesin A1 pasca overhaul",
            "description": (
                "Inspeksi komprehensif setelah overhaul besar. Semua sistem diperiksa: "
                "hidrolik, elektrik, pneumatik, dan mekanik. Hasil: semua sistem dalam "
                "kondisi baik. Mesin siap beroperasi kembali dengan kapasitas penuh."
            ),
            "type": "preventive", "priority": "high",
            "asset": press, "component": None,
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(100), "due_date": d(96), "completed_at": d(97),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER,
        },
        {
            "title": "Penggantian filter cartridge mesin press",
            "description": (
                "Filter cartridge sistem hidro-pneumatik sudah jenuh (indikator merah). "
                "Penggantian dilakukan on-site tanpa perlu membongkar sistem utama. "
                "Filter baru dipasang dan dites selama 30 menit tanpa kebocoran."
            ),
            "type": "corrective", "priority": "medium",
            "asset": press, "component": comps[1],
            "assigned_to": tech, "created_by_role": "admin",
            "created_at": d(5), "due_date": d(4), "completed_at": d(4),
            "initial_image": IMG_BEFORE, "evidence_image": IMG_AFTER_BLUE,
        },
        {
            "title": "Pemeriksaan bearing set CNC setelah alarm getaran",
            "description": (
                "Sistem monitoring mendeteksi peningkatan getaran pada sumbu Y. "
                "Inspeksi menemukan bearing dalam kondisi baik namun kurang pelumas. "
                "Pelumasan dilakukan dan alarm getaran tidak muncul kembali setelah 24 jam."
            ),
            "type": "corrective", "priority": "medium",
            "asset": cnc, "component": comps[5],
            "assigned_to": tech, "created_by_role": "manager",
            "created_at": d(3), "due_date": d(2), "completed_at": d(2),
            "initial_image": IMG_BEFORE_AMBER, "evidence_image": IMG_AFTER_TEAL,
        },
    ]


def seed():
    with app.app_context():
        press    = Asset.objects(machine_id='PR-001').first()
        cnc      = Asset.objects(machine_id='CNC-002').first()
        conveyor = Asset.objects(machine_id='CV-003').first()
        tech     = User.objects(email='tech@cmms.com').first()
        manager  = User.objects(email='manager@cmms.com').first()
        admin_u  = User.objects(email='admin@cmms.com').first()
        comps    = list(ComponentItem.objects())

        if not all([press, cnc, conveyor, tech]):
            print("ERROR: Jalankan seed_data.py terlebih dahulu untuk membuat aset dan user dasar.")
            return

        # Map komponen by name untuk index yang aman
        comp_map = {c.name: c for c in comps}
        comp_list = [
            comp_map.get('Hydraulic Pump'),
            comp_map.get('Filter Cartridge'),
            comp_map.get('Belt Drive'),
            comp_map.get('Lubricant Oil'),
            comp_map.get('Sensor Module'),
            comp_map.get('Bearing Set'),
            comp_map.get('Fan Blades'),
            comp_map.get('Pressure Valve'),
        ]

        entries = wo_entries(press, cnc, conveyor, tech, admin_u, manager, comp_list)

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
