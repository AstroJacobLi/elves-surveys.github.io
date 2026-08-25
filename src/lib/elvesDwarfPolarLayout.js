// Web translation of elves-dwarf-figure/make_elves_dwarf_polar.py.
// Geometry is calculated at build time, so the browser only has to render and
// interact with the resulting SVG nodes.

const D_MAX = 12;
const R_OUT = 5.3;
const FILL_FAN = 0.22;
const HOST_PAD = 0.085;
const SAT_MIN_SEP = 0.115;
const SAT_LOGM_MIN = 5;
const RPI = R_OUT / D_MAX;

const clamp = (value, low, high) => Math.min(Math.max(value, low), high);
const radians = (degrees) => degrees * Math.PI / 180;

const initialPositions = (hosts, radii) => {
  const positions = Array.from({ length: hosts.length });
  const shells = new Map();

  hosts.forEach((host, index) => {
    const shell = Math.floor(host.dist / 2);
    if (!shells.has(shell)) shells.set(shell, []);
    shells.get(shell).push(index);
  });

  for (const [shell, indices] of shells) {
    indices.sort((a, b) => hosts[b].logMstar - hosts[a].logMstar);
    const offset = (0.382 * shell) % 1;
    indices.forEach((index, rank) => {
      const fraction = ((rank + 0.5) / indices.length + offset) % 1;
      const theta = radians(8 + fraction * 164);
      const radial = hosts[index].dist * RPI;
      positions[index] = {
        x: radial * Math.cos(theta),
        y: radial * Math.sin(theta),
        radius: radii[index]
      };
    });
  }

  return positions;
};

const relax = (hosts, radii) => {
  const positions = initialPositions(hosts, radii);
  const radialTrue = hosts.map((host) => host.dist * RPI);
  const lower = hosts.map((host, index) => Math.max(
    radialTrue[index] - (host.dist < 2 ? 1 : 0.5) * RPI,
    radii[index] + 0.02
  ));
  const upper = hosts.map((host, index) => Math.min(
    radialTrue[index] + (host.dist < 2 ? 1 : 0.5) * RPI,
    R_OUT - radii[index] + 0.1
  ));

  for (let iteration = 0; iteration < 2500; iteration += 1) {
    for (let i = 0; i < positions.length; i += 1) {
      for (let j = i + 1; j < positions.length; j += 1) {
        let dx = positions[i].x - positions[j].x;
        let dy = positions[i].y - positions[j].y;
        let distance = Math.hypot(dx, dy);
        const minimum = radii[i] + radii[j] + HOST_PAD;

        if (distance < minimum) {
          if (distance < 1e-9) {
            dx = Math.cos((i + 1) * (j + 2));
            dy = Math.sin((i + 1) * (j + 2));
            distance = 1;
          }
          const push = 0.5 * (minimum - distance) / distance;
          positions[i].x += push * dx;
          positions[i].y += push * dy;
          positions[j].x -= push * dx;
          positions[j].y -= push * dy;
        }
      }
    }

    positions.forEach((position, index) => {
      let radial = Math.max(Math.hypot(position.x, position.y), 1e-6);
      const target = clamp(radial, lower[index], upper[index]);
      const correction = 1 + 0.85 * (target / radial - 1);
      position.x *= correction;
      position.y *= correction;

      radial = Math.max(Math.hypot(position.x, position.y), radii[index] + 0.02);
      const minimumAngle = Math.asin(clamp((radii[index] + 0.02) / radial, 0, 1));
      const angle = clamp(Math.atan2(position.y, position.x), minimumAngle, Math.PI - minimumAngle);
      position.x = radial * Math.cos(angle);
      position.y = radial * Math.sin(angle);
    });
  }

  let worstGap = 0;
  for (let i = 0; i < positions.length; i += 1) {
    for (let j = i + 1; j < positions.length; j += 1) {
      worstGap = Math.min(
        worstGap,
        Math.hypot(positions[i].x - positions[j].x, positions[i].y - positions[j].y)
          - radii[i] - radii[j]
      );
    }
  }

  return { positions, worstGap };
};

const hostAngleOffset = (name) => {
  let hash = 2166136261;
  for (const character of name) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) / 4294967296) * Math.PI * 2;
};

// Samples from Matplotlib's rainbow_r colormap, which is used by the Python
// figure. Interpolation between the samples keeps the browser and paper
// versions visually consistent without shipping a plotting dependency.
const RAINBOW_R = [
  [255, 0, 0],
  [255, 98, 50],
  [254, 181, 98],
  [190, 236, 142],
  [126, 255, 181],
  [63, 235, 213],
  [1, 179, 236],
  [66, 95, 250],
  [128, 0, 255]
];

const satelliteColor = (logMass) => {
  if (!Number.isFinite(logMass)) return '#7f8a99';
  const fraction = clamp((logMass - 5) / 4, 0, 1);
  const scaled = fraction * (RAINBOW_R.length - 1);
  const left = Math.floor(scaled);
  const right = Math.min(left + 1, RAINBOW_R.length - 1);
  const mix = scaled - left;
  const rgb = RAINBOW_R[left].map((value, channel) => Math.round(
    value + (RAINBOW_R[right][channel] - value) * mix
  ));
  return `rgb(${rgb.join(' ')})`;
};

const placeSatellites = (host, radius) => {
  const satellites = host.sats
    .filter((satellite) => ['Confirmed', 'Unconfirmed', 'Not Observed'].includes(satellite.status))
    .filter((satellite) => satellite.logM === null || satellite.logM > SAT_LOGM_MIN)
    .map((satellite) => ({ ...satellite }));
  const effectiveRadius = Math.max(radius - 0.085, 0.35 * radius);
  const order = satellites
    .map((satellite, index) => ({
      index,
      radial: clamp(satellite.d_proj_rvir ?? 0.1, 0.1, 1) * effectiveRadius
    }))
    .sort((a, b) => b.radial - a.radial);
  const angles = Array(satellites.length).fill(0);
  const offset = hostAngleOffset(host.name);

  order.forEach((entry, rank) => {
    let theta = offset + radians(137.508) * rank;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      const x = entry.radial * Math.cos(theta);
      const y = entry.radial * Math.sin(theta);
      const clear = order.slice(0, rank).every((previous) => {
        const px = previous.radial * Math.cos(angles[previous.index]);
        const py = previous.radial * Math.sin(angles[previous.index]);
        return Math.hypot(x - px, y - py) >= SAT_MIN_SEP;
      });
      if (clear) break;
      theta += radians(23);
    }
    angles[entry.index] = theta;
  });

  return satellites.map((satellite, index) => {
    const radial = clamp(satellite.d_proj_rvir ?? 0.1, 0.1, 1) * effectiveRadius;
    return {
      ...satellite,
      x: radial * Math.cos(angles[index]),
      y: radial * Math.sin(angles[index]),
      color: satelliteColor(satellite.logM)
    };
  });
};

export const buildElvesDwarfPolarLayout = (inputHosts) => {
  const hosts = inputHosts.map((host) => ({
    ...host,
    dist: Number(host.dist),
    logMstar: Number(host.logMstar),
    rvir: Number(host.rvir)
  }));
  const diskArea = Math.PI * R_OUT ** 2 * 0.5;
  const virialArea = Math.PI * hosts.reduce((sum, host) => sum + host.rvir ** 2, 0);
  let scale = Math.sqrt(FILL_FAN * diskArea / virialArea);
  let result;
  let radii;

  for (let attempt = 0; attempt < 8; attempt += 1) {
    radii = hosts.map((host) => host.rvir * scale);
    result = relax(hosts, radii);
    if (result.worstGap > -0.02) break;
    scale *= 0.95;
  }

  const laidOutHosts = hosts.map((host, index) => {
    const satellites = placeSatellites(host, radii[index]);
    const count = (status) => satellites.filter((satellite) => satellite.status === status).length;
    return {
      ...host,
      x: result.positions[index].x,
      y: result.positions[index].y,
      radius: radii[index],
      isLiterature: String(host.data_source).startsWith('\\citetalias'),
      satellites,
      counts: {
        confirmed: count('Confirmed'),
        unconfirmed: count('Unconfirmed'),
        notObserved: count('Not Observed')
      }
    };
  });

  return {
    dMax: D_MAX,
    rOut: R_OUT,
    rpi: RPI,
    rings: [4, 8, 12],
    hosts: laidOutHosts,
    shownSatellites: laidOutHosts.reduce((sum, host) => sum + host.satellites.length, 0),
    worstGap: result.worstGap
  };
};
