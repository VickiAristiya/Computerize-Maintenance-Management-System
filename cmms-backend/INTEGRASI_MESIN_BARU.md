# Integrasi Model ML Mesin Baru — Jalur Cepat

Target: dari model selesai dilatih sampai tampil di dashboard CMMS dalam
**± 15 menit**, tanpa menulis file predictor baru dan tanpa mengubah skema
database atau front-end.

Sebelumnya (kompresor, induksi, forging, bor) tiap mesin butuh 5 file disentuh:
predictor baru ±220 baris, `ml_registry.py`, `models.py`, `ml_routes.py`, dan
`SensorMonitoringPage.jsx`. Sekarang cukup **1 entri registry + file model**.

---

## Langkah 1 — Export model dari notebook (paling penting)

Backend membaca nama fitur, nama komponen, dan label kelas **langsung dari
bundle `.pkl`**. Jadi selama notebook menyimpan dengan format di bawah,
backend tidak perlu tahu apa-apa lagi tentang mesin ini.

Simpan ke `machine-learning filtered data/<folder>/models/`:

| File | Isi |
| --- | --- |
| `hybrid_model_<komponen>.pkl` | dict: `scaler`, `svm`, `feature_columns`, `class_names` |
| `dnn_extractor_<komponen>.keras` | model Keras pengekstrak fitur laten |

```python
joblib.dump(
    {
        "scaler": scaler,                    # MinMaxScaler yang sudah di-fit
        "svm": svm,                          # SVC(probability=True)
        "feature_columns": feature_columns,  # urutan kolom WAJIB sama dgn saat training
        "class_names": class_names,          # [label_normal, label_fault] — indeks 0 = normal
        "target_column": target_column,
        "label_mapping": label_map,
        "metrics": metrics,
    },
    models_dir / f"hybrid_model_{target_column}.pkl",
)
feature_extractor.save(models_dir / f"dnn_extractor_{target_column}.keras")
```

Dua aturan yang kalau dilanggar bikin hasil prediksi salah diam-diam:

1. **`class_names[0]` harus kelas normal, `class_names[1]` kelas fault.**
   Backend memakai `predict_proba(...)[1]` sebagai `failure_probability`.
2. **Nama di `feature_columns` = nama field yang dikirim sensor.** Kalau
   berbeda (sensor kirim `temp`, model dilatih `temp_c`), daftarkan di
   `aliases` pada Langkah 2 — jangan ganti nama kolom di notebook setelah
   model di-fit.

Nama komponen bebas (`status`, `bearings`, `spindle`, …) dan boleh lebih dari
satu — backend mendeteksinya otomatis dari nama file `hybrid_model_*.pkl`.

## Langkah 2 — Daftarkan di `app/ml_registry.py`

Satu entri di dict `MACHINES`:

```python
MACHINES: dict[str, dict] = {
    "CNC-001": {
        "folder": "cnc",                          # nama subfolder di machine-learning filtered data/
        "label": "Mesin CNC",
        "component_names": {"status": "Spindle & Servo"},
        "fault_message": "Mesin CNC terindikasi fault — periksa spindle dan servo drive.",
        # "aliases": {"temp_c": ["temp", "suhu"]},   # hanya kalau nama field sensor beda
    },
}
```

Wajib: `folder`, `label`. Sisanya opsional — tanpa itu pun prediksi tetap
jalan, hanya teks rekomendasinya generik.

## Langkah 3 — Verifikasi sebelum menyalakan backend

```bash
cd cmms-backend
venv/Scripts/python.exe -m scripts.cek_mesin CNC-001
```

Script memeriksa registry → kelengkapan file → isi bundle → menjalankan smoke
test inferensi, lalu mencetak daftar field sensor, contoh payload JSON, dan
blok `SENSOR_FIELDS` siap tempel untuk simulator. Kalau semua `[OK]`,
integrasi backend sudah selesai.

## Langkah 4 — Aset & simulator

1. **Aset di database** — pastikan ada aset dengan `machine_id` yang sama
   persis (lewat menu Aset di front-end, atau `seed_data.py`). Ini satu-satunya
   langkah yang tidak bisa diotomatiskan.
2. **Simulator** — di `Simulasi/Version 2/simulasi-input data/config.py`,
   ganti `MACHINE_ID` dan tempel blok `SENSOR_FIELDS` hasil Langkah 3.
   `PRESETS` boleh dikosongkan jadi `[{"id": "manual", "label": "Input Manual",
   "description": "Isi nilai sensor secara manual", "data": None}]`.

Selesai. Kirim satu data sensor dari simulator, lalu buka halaman Monitoring
Sensor mesin tersebut.

---

## Yang sudah tidak perlu disentuh lagi

| Berkas | Kenapa aman ditinggal |
| --- | --- |
| `app/predictors/*.py` | `GenericHybridPredictor` menangani semua mesin baru |
| `app/models.py` (`SensorData`) | field yang belum punya kolom resmi masuk ke `raw_readings`, dan inferensi + `/predict/<machine_id>` sudah membaca dari sana |
| `app/api/ml_routes.py` | alias field dibaca dari `MACHINES["…"]["aliases"]` |
| `SensorMonitoringPage.jsx` | field tak dikenal dapat label/warna otomatis; menambah entri `FIELD_META` sifatnya kosmetik saja |

Catatan: menambahkan field ke `SensorData` tetap berguna kalau kolom itu mau
dipakai untuk query/agregasi khusus — tapi bukan syarat agar prediksi jalan.

## Kalau macet

| Gejala | Penyebab paling sering |
| --- | --- |
| `belum terdaftar di ml_registry.py` | `machine_id` di entri `MACHINES` beda dengan yang di database/simulator (case-sensitive) |
| `File model belum lengkap` | nama folder atau nama file tidak sesuai pola `hybrid_model_<komponen>.pkl` |
| `missing_features` saat kirim sensor | nama field sensor ≠ `feature_columns` → tambahkan `aliases` |
| Prediksi selalu fault / selalu normal | urutan `class_names` terbalik saat training |
| Health score tidak muncul di dashboard | aset dengan `machine_id` itu belum ada di database |
