
# 🏭 CMMS for Manufacturing (Computerized Maintenance Management System)

![Project Status](https://img.shields.io/badge/Status-Feature%20Complete-success?style=for-the-badge)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**Sistem manajemen pemeliharaan berbasis web tingkat lanjut** yang dirancang khusus untuk lingkungan manufaktur. Aplikasi ini mengintegrasikan pelacakan aset, manajemen inventaris, dan alur kerja (workflow) pemeliharaan yang ketat—mulai dari pengajuan, pengerjaan, hingga verifikasi akhir dengan bukti digital.

---

## 🚀 Fitur Utama & Kapabilitas

Sistem ini dibangun dengan logika bisnis yang komprehensif untuk menangani kebutuhan industri nyata.

| Modul | Fungsionalitas & Logika Bisnis |
| :--- | :--- |
| **🔐 Authentication & RBAC** | Kontrol akses berbasis peran (**Admin**, **Manager**, **Technician**). Teknisi memiliki akses terbatas hanya untuk eksekusi tugas. |
| **📋 Work Order (WO)** | Siklus hidup penuh: `Open` → `In Progress` → `Pending Verification` → `Completed`. Mendukung `Pending Approval` untuk WO dari Manager. |
| **✅ Sistem Verifikasi** | **Validasi Ganda:** Teknisi wajib upload **Foto Bukti Selesai**. Admin/Manager wajib memverifikasi foto sebelum menutup WO. |
| **📦 Gudang Pintar** | Stok komponen terkoneksi dengan WO. Stok hanya **berkurang otomatis** setelah status WO diverifikasi menjadi *Completed*. |
| **🏭 Manajemen Aset** | Pelacakan status mesin *real-time* (**Running** / **Down**). Mendukung upload foto aset dan *Bill of Materials* (BOM). |
| **📊 Smart Dashboard** | **Pusat Komando** dengan notifikasi interaktif. Menampilkan peringatan H-7 jadwal maintenance, stok menipis, dan WO tertunda. |
| **🔔 Notifikasi** | Ikon lonceng interaktif untuk memberitahu Admin/Manager tentang tugas mendesak dan persetujuan yang menunggu. |
| **📄 Laporan** | Format waktu otomatis **WIB**. Ekspor laporan kinerja aset dan riwayat perbaikan ke **PDF** dan **CSV**. |

---

## 🔄 Alur Kerja (Standard Operating Procedure)

Sistem ini menerapkan SOP pemeliharaan standar industri untuk menjamin akuntabilitas.

### 1. Inisiasi (Pembuatan WO)
* **Admin:** WO langsung berstatus `OPEN`.
* **Manager:** WO berstatus `PENDING APPROVAL` (Menunggu persetujuan Admin).
* **Technician:** *Read-only* (Tidak diizinkan membuat WO).
* *Requirement:* Wajib menyertakan **Foto Awal (Masalah)** saat pembuatan.

### 2. Eksekusi (Pengerjaan)
* Teknisi menerima tugas di dashboard mereka.
* Teknisi menekan tombol **"Mulai"** → Status berubah menjadi `IN PROGRESS`.
* Sistem mencatat waktu mulai dan nama teknisi secara otomatis.

### 3. Pelaporan (Penyelesaian)
* Setelah perbaikan selesai, Teknisi **WAJIB** mengunggah **Foto Bukti Perbaikan**.
* Status berubah menjadi `PENDING VERIFICATION`.

### 4. Validasi & Penutupan
* Admin/Manager menerima notifikasi verifikasi.
* Admin membandingkan **Foto Awal** vs **Foto Bukti**.
* Jika valid, Admin menekan **"Verifikasi Selesai"**.
* Status menjadi `COMPLETED` dan stok sparepart di gudang **otomatis berkurang**.

---

## 🏗️ Arsitektur Teknologi

Aplikasi dibangun dengan arsitektur terpisah (*decoupled*) untuk performa dan skalabilitas maksimal.

| Layer | Teknologi | Deskripsi |
| :--- | :--- | :--- |
| **Frontend** | React, Vite, Tailwind CSS | UI modern dengan `Context API` untuk manajemen state dan `Axios` untuk komunikasi HTTP. Menggunakan ikon dari `Lucide React`. |
| **Backend** | Python, Flask | REST API yang cepat. Menggunakan `Flask-Bcrypt` untuk keamanan hashing password. |
| **Database** | MongoDB, MongoEngine | Database NoSQL untuk menangani struktur data aset yang dinamis dan kompleks. |
| **Reporting** | ReportLab, CSV | Engine untuk generate laporan PDF otomatis di sisi server. |

---

## ⚙️ Panduan Instalasi (Local Setup)

Sistem ini menggunakan arsitektur Client-Server yang membutuhkan **dua terminal** berjalan secara bersamaan.

### Prasyarat
* [Python 3.8+](https://www.python.org/)
* [Node.js & npm](https://nodejs.org/)
* [MongoDB](https://www.mongodb.com/) (Pastikan service MongoDB berjalan di port default `27017`)

### 1. Setup Backend (Terminal 1)

Buka terminal pertama, lalu ikuti langkah ini untuk menjalankan server API.

```bash
# 1. Masuk ke direktori backend
cd cmms-backend

# 2. Buat & Aktifkan Virtual Environment
# Windows:
python -m venv venv
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Instal Dependencies
pip install -r requirements.txt

# 4. Isi Database dengan Data Dummy
python seed_data.py

# 5. Jalankan Server
python run.py
````

> ✅ **Status:** Server Backend berjalan di `http://127.0.0.1:5000`.
>
> ⚠️ **PENTING:** Biarkan terminal ini tetap terbuka. Jangan ditutup selama aplikasi digunakan.

### 2\. Setup Frontend (Terminal 2)

Buka **Terminal Baru (New Terminal)**. Jangan gunakan terminal yang sedang menjalankan backend.

```bash
# 1. Masuk ke direktori frontend
cd cmms-frontend

# 2. Instal Node Modules (Hanya perlu dilakukan sekali)
npm install

# 3. Jalankan Mode Pengembangan
npm run dev
```

> ✅ **Status:** Aplikasi Frontend berjalan di `http://localhost:5173`.
>
> 💡 **Info:** Frontend akan otomatis terhubung ke Backend yang berjalan di Terminal 1.

-----

## 🔑 Akun Demo (Default Seeder)

Jika Anda telah melakukan *seeding* database, gunakan kredensial berikut:

  * **Admin:** `admin@cmms.com` / `password123`
  * **Manager:** `manager@cmms.com` / `password123`
  * **Technician:** `tech@cmms.com` / `password123`

-----

## 📂 Struktur Direktori

```text
root/
├── cmms-backend/       # Server Side Logic (Flask API)
│   ├── models/         # Skema Database (MongoEngine)
│   ├── routes/         # Endpoint API
│   ├── static/         # Penyimpanan file upload (Foto)
│   └── run.py          # Entry point aplikasi
│
└── cmms-frontend/      # Client Side Logic (React)
    ├── src/
    │   ├── components/ # UI Components reusable
    │   ├── pages/      # Halaman utama (Dashboard, WO, dll)
    │   └── context/    # Auth Context
    └── package.json
```

```
```