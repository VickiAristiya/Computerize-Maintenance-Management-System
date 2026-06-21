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
    data: null, // null = form kosong
  },
  {
    id: "normal",
    label: "Normal — Semua OK",
    description: "Semua komponen dalam kondisi baik (Ok P50 dataset)",
    icon: "check",
    color: "green",
    data: {
      rpm: 1500.0, motor_power: 5874.43, noise_db: 51.51,
      outlet_pressure_bar: 4.018, air_flow: 600.15, outlet_temp: 119.37,
      wpump_outlet_press: 2.80, water_flow: 55.81, gaccz: 3.59, haccz: 3.32,
    },
  },
  {
    id: "bearing_fault",
    label: "Bearing Fault",
    description: "Bearing Noisy — noise_db tinggi + air_flow tinggi",
    icon: "alert",
    color: "purple",
    // Dari eksplorasi: BRG FP=100%, WPU<1%, RAD<1%, EXV<1%
    data: {
      rpm: 2003.0, motor_power: 10768.67, noise_db: 63.31,
      outlet_pressure_bar: 4.92, air_flow: 1198.22, outlet_temp: 125.49,
      wpump_outlet_press: 2.39, water_flow: 58.30, gaccz: 4.15, haccz: 3.55,
    },
  },
  {
    id: "wpump_fault",
    label: "Water Pump Fault",
    description: "Water Pump Noisy — air_flow & outlet_temp tinggi",
    icon: "alert",
    color: "blue",
    // Dari eksplorasi: BRG<1%, WPU FP=99.7%, RAD<1%, EXV<1%
    data: {
      rpm: 1517.0, motor_power: 11001.14, noise_db: 56.11,
      outlet_pressure_bar: 6.66, air_flow: 883.37, outlet_temp: 138.26,
      wpump_outlet_press: 2.89, water_flow: 50.51, gaccz: 6.23, haccz: 4.63,
    },
  },
  {
    id: "radiator_fault",
    label: "Radiator Fault",
    description: "Radiator Dirty — water_flow sangat rendah",
    icon: "alert",
    color: "green",
    // Dari eksplorasi: BRG<1%, WPU<1%, RAD FP=100%, EXV<1%
    data: {
      rpm: 1503.0, motor_power: 2634.21, noise_db: 50.48,
      outlet_pressure_bar: 1.15, air_flow: 803.44, outlet_temp: 110.18,
      wpump_outlet_press: 2.28, water_flow: 41.20, gaccz: 1.91, haccz: 2.50,
    },
  },
  {
    id: "exvalve_fault",
    label: "Exhaust Valve Fault",
    description: "Exhaust Valve Dirty — air_flow rendah + rpm tinggi",
    icon: "alert",
    color: "orange",
    // Dari eksplorasi: BRG<1%, WPU<1%, RAD<1%, EXV FP=100%
    data: {
      rpm: 2496.0, motor_power: 7509.70, noise_db: 61.87,
      outlet_pressure_bar: 2.65, air_flow: 492.45, outlet_temp: 123.18,
      wpump_outlet_press: 2.56, water_flow: 58.13, gaccz: 2.35, haccz: 2.66,
    },
  },
  {
    id: "bearing_wpump_fault",
    label: "Bearing + Water Pump Fault",
    description: "2 komponen fault — noise tinggi + air_flow sangat tinggi",
    icon: "alert",
    color: "red",
    // Dari eksplorasi: BRG FP=100%, WPU FP=99%, RAD~26%, EXV<1%
    data: {
      rpm: 707.6, motor_power: 9250.9, noise_db: 55.5,
      outlet_pressure_bar: 8.3, air_flow: 1360.5, outlet_temp: 102.1,
      wpump_outlet_press: 3.07, water_flow: 42.25, gaccz: 8.56, haccz: 5.62,
    },
  },
  {
    id: "radiator_exvalve_fault",
    label: "Radiator + Exhaust Valve Fault",
    description: "2 komponen fault — air_flow sangat rendah + rpm sangat tinggi",
    icon: "alert",
    color: "red",
    // Dari eksplorasi: BRG~20%, WPU<1%, RAD FP=54%, EXV FP=100%
    data: {
      rpm: 2515.0, motor_power: 10600.5, noise_db: 43.0,
      outlet_pressure_bar: 1.36, air_flow: 253.5, outlet_temp: 137.0,
      wpump_outlet_press: 3.78, water_flow: 47.27, gaccz: 2.21, haccz: 3.77,
    },
  },
  {
    id: "bearing_radiator_fault",
    label: "Bearing + Radiator Fault",
    description: "2 komponen fault — noise tinggi + water_flow rendah",
    icon: "alert",
    color: "red",
    // Dari eksplorasi: BRG FP=82%, WPU<1%, RAD FP=100%, EXV<1%
    data: {
      rpm: 929.7, motor_power: 12039.9, noise_db: 67.8,
      outlet_pressure_bar: 1.0, air_flow: 1259.4, outlet_temp: 111.5,
      wpump_outlet_press: 2.95, water_flow: 41.86, gaccz: 7.45, haccz: 5.42,
    },
  },
];

export const SENSOR_FIELD_GROUPS = [
  {
    group: 'Motor & Drive',
    fields: [
      { key: 'rpm',         label: 'RPM',          unit: 'RPM' },
      { key: 'motor_power', label: 'Motor Power',  unit: 'W' },
    ],
  },
  {
    group: 'Udara Terkompresi',
    fields: [
      { key: 'outlet_pressure_bar', label: 'Tekanan Outlet', unit: 'bar' },
      { key: 'air_flow',            label: 'Aliran Udara',   unit: 'm³/h' },
      { key: 'noise_db',            label: 'Kebisingan',     unit: 'dB' },
      { key: 'outlet_temp',         label: 'Suhu Outlet',    unit: '°C' },
    ],
  },
  {
    group: 'Sistem Pendingin',
    fields: [
      { key: 'wpump_outlet_press', label: 'Tekanan Pompa Air', unit: 'bar' },
      { key: 'water_flow',         label: 'Aliran Air',        unit: 'L/min' },
    ],
  },
  {
    group: 'Akselerometer',
    fields: [
      { key: 'gaccz', label: 'G-Axis Akselerasi Z', unit: 'g' },
      { key: 'haccz', label: 'H-Axis Akselerasi Z', unit: 'g' },
    ],
  },
];

export const DUMMY_COMPRESSOR = {
  name: "Dummy Compressor ML Test Rig",
  machine_id: "CMP-DUMMY-001",
  location: "Area Produksi - Simulasi ML",
  status: "running",
};
