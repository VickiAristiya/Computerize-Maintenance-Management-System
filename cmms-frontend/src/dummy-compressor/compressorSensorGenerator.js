const OK_SAMPLE = {
  rpm: 499,
  motor_power: 1405.842858,
  torque: 27.51170834,
  outlet_pressure_bar: 1,
  air_flow: 308.2898788,
  noise_db: 40.84051681,
  outlet_temp: 78.55471462,
  wpump_outlet_press: 2.960632487,
  water_inlet_temp: 43.16639156,
  water_outlet_temp: 47.25923766,
  wpump_power: 216.6105061,
  water_flow: 59.0850591,
  oilpump_power: 300.3729213,
  oil_tank_temp: 45.80617755,
  gaccx: 0.711820164,
  gaccy: 0.383772955,
  gaccz: 2.649800567,
  haccx: 1.213344407,
  haccy: 1.409218131,
  haccz: 2.962483674,
};

const NOISY_SAMPLE = {
  rpm: 500,
  motor_power: 1402.424603,
  torque: 26.91957192,
  outlet_pressure_bar: 1,
  air_flow: 308.2705663,
  noise_db: 45.46106943,
  outlet_temp: 78.29331063,
  wpump_outlet_press: 2.331081334,
  water_inlet_temp: 43.78669864,
  water_outlet_temp: 48.32915461,
  wpump_power: 215.7832218,
  water_flow: 59.17499154,
  oilpump_power: 300.9885927,
  oil_tank_temp: 45.87909428,
  gaccx: 0.70000561,
  gaccy: 0.389492342,
  gaccz: 2.644748976,
  haccx: 1.209735291,
  haccy: 1.439140959,
  haccz: 2.974438125,
};

const randomBetween = (min, max) => min + Math.random() * (max - min);

const DEMO_STAGES = [
  { ratio: 0.45, label: "Normal", expectedRisk: "< 10%", expectedAction: "90 hari" },
  { ratio: 0.54361, label: "Risiko rendah", expectedRisk: "10-29%", expectedAction: "60 hari" },
  { ratio: 0.57462, label: "Risiko sedang", expectedRisk: "30-49%", expectedAction: "30 hari" },
  { ratio: 0.61334, label: "Risiko tinggi", expectedRisk: "50-79%", expectedAction: "7 hari" },
  { ratio: 0.65037, label: "Kritis", expectedRisk: ">= 80%", expectedAction: "segera" },
];

const SENSOR_MODES = {
  normal: [DEMO_STAGES[0]],
  maintenance_low: [DEMO_STAGES[1]],
  maintenance_medium: [DEMO_STAGES[2]],
  maintenance_high: [DEMO_STAGES[3]],
  maintenance_critical: [DEMO_STAGES[4]],
};

const blend = (from, to, ratio, addNoise = false) => {
  const blended = {};
  Object.keys(from).forEach((key) => {
    const value = from[key] + (to[key] - from[key]) * ratio;
    const noise = addNoise ? Math.abs(value) * randomBetween(-0.001, 0.001) : 0;
    blended[key] = Number((value + noise).toFixed(6));
  });
  return blended;
};

export function generateCompressorSensorPayload(assetId, tick, mode = "normal") {
  const stages = SENSOR_MODES[mode] || SENSOR_MODES.normal;
  const stage = stages[Math.floor(tick / 2) % stages.length];
  const ratio = stage.ratio;
  const blended = blend(OK_SAMPLE, NOISY_SAMPLE, ratio, true);

  return {
    asset_id: assetId,
    demo_mode: mode,
    demo_stage: stage.label,
    demo_expected_risk: stage.expectedRisk,
    demo_expected_action: stage.expectedAction,
    temperature: Number(blended.outlet_temp.toFixed(2)),
    vibration: Number(blended.gaccz.toFixed(3)),
    pressure: Number(blended.outlet_pressure_bar.toFixed(3)),
    current: Number(randomBetween(13.5, 16.5).toFixed(2)),
    voltage: Number(randomBetween(392, 406).toFixed(2)),
    ...blended,
  };
}

export const DUMMY_COMPRESSOR = {
  name: "Dummy Compressor Bearing Test Rig",
  machine_id: "CMP-DUMMY-001",
  location: "Area Produksi - Simulasi ML",
  status: "running",
};

export function getTemplateData(mode) {
  const stages = SENSOR_MODES[mode] || SENSOR_MODES.normal;
  const stage = stages[0];
  const blended = blend(OK_SAMPLE, NOISY_SAMPLE, stage.ratio, false);
  return {
    ...blended,
    current: 15.0,
    voltage: 399.0,
  };
}

export const SENSOR_FIELD_GROUPS = [
  {
    group: 'Motor & Drive',
    fields: [
      { key: 'rpm', label: 'RPM', unit: 'RPM' },
      { key: 'motor_power', label: 'Motor Power', unit: 'W' },
      { key: 'torque', label: 'Torque', unit: 'Nm' },
      { key: 'current', label: 'Arus', unit: 'A' },
      { key: 'voltage', label: 'Tegangan', unit: 'V' },
    ],
  },
  {
    group: 'Udara Terkompresi',
    fields: [
      { key: 'outlet_pressure_bar', label: 'Tekanan Outlet', unit: 'bar' },
      { key: 'air_flow', label: 'Aliran Udara', unit: 'm³/h' },
      { key: 'noise_db', label: 'Kebisingan', unit: 'dB' },
      { key: 'outlet_temp', label: 'Suhu Outlet', unit: '°C' },
    ],
  },
  {
    group: 'Sistem Pendingin',
    fields: [
      { key: 'wpump_outlet_press', label: 'Tekanan Pompa Air', unit: 'bar' },
      { key: 'water_inlet_temp', label: 'Suhu Air Masuk', unit: '°C' },
      { key: 'water_outlet_temp', label: 'Suhu Air Keluar', unit: '°C' },
      { key: 'wpump_power', label: 'Daya Pompa Air', unit: 'W' },
      { key: 'water_flow', label: 'Aliran Air', unit: 'L/min' },
    ],
  },
  {
    group: 'Sistem Oli',
    fields: [
      { key: 'oilpump_power', label: 'Daya Pompa Oli', unit: 'W' },
      { key: 'oil_tank_temp', label: 'Suhu Tangki Oli', unit: '°C' },
    ],
  },
  {
    group: 'Akselerometer G-Axis',
    fields: [
      { key: 'gaccx', label: 'Akselerasi X', unit: 'g' },
      { key: 'gaccy', label: 'Akselerasi Y', unit: 'g' },
      { key: 'gaccz', label: 'Akselerasi Z', unit: 'g' },
    ],
  },
  {
    group: 'Akselerometer H-Axis',
    fields: [
      { key: 'haccx', label: 'Akselerasi X', unit: 'g' },
      { key: 'haccy', label: 'Akselerasi Y', unit: 'g' },
      { key: 'haccz', label: 'Akselerasi Z', unit: 'g' },
    ],
  },
];
