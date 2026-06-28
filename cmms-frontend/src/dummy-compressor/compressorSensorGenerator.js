/**
 * Template nilai sensor berdasarkan hasil eksplorasi model ML.
 * Setiap template dipilih dari sampel dataset/random yang menghasilkan
 * fault probability tinggi pada komponen target dan rendah pada komponen lain.
 */

export const SENSOR_TEMPLATES = [
  {
    id: "manual",
    label: "Input Manual",
    description: "Isi nilai sensor secara manual",
    icon: "pencil",
    color: "slate",
    data: null,
  },
  {
    id: "normal",
    label: "Normal — Bearing OK",
    description: "Bearing sehat — fault probability ~0% (very low risk)",
    icon: "check",
    color: "green",
    // fault_prob ≈ 0.0000 [very_low]
    data: {
      noise_db: 51.50, water_flow: 58.11, air_flow: 600.0,
      gaccx: 0.5768, outlet_temp: 118.28,
    },
  },
  {
    id: "bearing_low",
    label: "Bearing — Risiko Ringan",
    description: "Bearing mulai tidak normal — fault probability ~11% (low risk)",
    icon: "alert",
    color: "blue",
    // fault_prob ≈ 0.1060 [low]
    data: {
      noise_db: 57.50, water_flow: 58.11, air_flow: 600.0,
      gaccx: 0.5768, outlet_temp: 118.28,
    },
  },
  {
    id: "bearing_medium",
    label: "Bearing — Risiko Sedang",
    description: "Bearing terindikasi fault — fault probability ~37% (medium risk)",
    icon: "alert",
    color: "orange",
    // fault_prob ≈ 0.3711 [medium]
    data: {
      noise_db: 58.00, water_flow: 58.11, air_flow: 600.0,
      gaccx: 0.5768, outlet_temp: 118.28,
    },
  },
  {
    id: "bearing_high",
    label: "Bearing — Risiko Tinggi",
    description: "Bearing fault signifikan — fault probability ~70% (high risk)",
    icon: "alert",
    color: "red",
    // fault_prob ≈ 0.7042 [high]
    data: {
      noise_db: 57.00, water_flow: 58.11, air_flow: 650.0,
      gaccx: 0.5768, outlet_temp: 118.28,
    },
  },
  {
    id: "bearing_critical",
    label: "Bearing — Kritis",
    description: "Bearing kritis — fault probability ~99% (critical risk)",
    icon: "alert",
    color: "red",
    // fault_prob ≈ 0.9947 [critical]
    data: {
      noise_db: 58.00, water_flow: 58.11, air_flow: 700.0,
      gaccx: 0.5768, outlet_temp: 118.28,
    },
  },
];

export const SENSOR_FIELD_GROUPS = [
  {
    group: 'Sensor Bearing',
    fields: [
      { key: 'noise_db',    label: 'Kebisingan',          unit: 'dB' },
      { key: 'water_flow',  label: 'Aliran Air',           unit: 'L/min' },
      { key: 'air_flow',    label: 'Aliran Udara',         unit: 'm³/h' },
      { key: 'gaccx',       label: 'G-Axis Akselerasi X',  unit: 'g' },
      { key: 'outlet_temp', label: 'Suhu Outlet',          unit: '°C' },
    ],
  },
];

export const DUMMY_COMPRESSOR = {
  name: "Dummy Compressor ML Test Rig",
  machine_id: "CMP-DUMMY-001",
  location: "Area Produksi - Simulasi ML",
  status: "running",
};
