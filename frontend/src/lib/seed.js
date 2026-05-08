// Seed data for the demo: synthetic complaints, ward boundaries (centroids),
// agencies, councillors. In production these come from BBMP open data,
// scraped officer lists, and the Twitter handle registry.

export const WARDS = [
  { id: 95,  name: 'Yelahanka',    ll: [13.0995, 77.5963], councillor: 'S. Rajeshwari',  tone: 'olive',  open: 312,  resolution: 0.82, avg: 5.1 },
  { id: 174, name: 'HSR Layout',   ll: [12.9116, 77.6473], councillor: 'M. Bhaskar Rao', tone: 'olive',  open: 428,  resolution: 0.71, avg: 7.4 },
  { id: 80,  name: 'Indiranagar',  ll: [12.9716, 77.6412], councillor: 'P. Srinivas',    tone: 'olive',  open: 611,  resolution: 0.64, avg: 9.2 },
  { id: 151, name: 'Koramangala',  ll: [12.9352, 77.6245], councillor: 'A. Chandrika',   tone: 'beige',  open: 738,  resolution: 0.58, avg: 11.8 },
  { id: 167, name: 'Jayanagar',    ll: [12.9250, 77.5938], councillor: 'K. Murthy',      tone: 'beige',  open: 502,  resolution: 0.51, avg: 13.0 },
  { id: 18,  name: 'Hebbal',       ll: [13.0392, 77.5970], councillor: 'V. Lakshmi',     tone: 'coffee', open: 1671, resolution: 0.14, avg: 29.4 },
  { id: 145, name: 'Whitefield',   ll: [12.9698, 77.7500], councillor: 'R. Krishnan',    tone: 'olive',  open: 187,  resolution: 0.69, avg: 8.9 },
  { id: 100, name: 'Rajajinagar',  ll: [12.9908, 77.5526], councillor: 'D. Padma',       tone: 'beige',  open: 264,  resolution: 0.55, avg: 12.4 },
  { id: 86,  name: 'Mahadevapura', ll: [12.9908, 77.6951], councillor: 'R. Nagaraj',     tone: 'coffee', open: 1240, resolution: 0.22, avg: 24.6 },
  { id: 188, name: 'Bommanahalli', ll: [12.9009, 77.6189], councillor: 'D. Gopala',      tone: 'coffee', open: 1422, resolution: 0.19, avg: 26.8 }
];

export const AGENCIES = [
  { code: 'BBMP-ROADS',  name: 'BBMP · Roads',           handle: '@BBMPCOMM',          email: 'jc.roads@bbmp.gov.in' },
  { code: 'BBMP-SWM',    name: 'BBMP · Solid Waste',     handle: '@BBMPCOMM',          email: 'swm@bbmp.gov.in' },
  { code: 'BBMP-ELEC',   name: 'BBMP · Electrical',      handle: '@BBMPCOMM',          email: 'electrical@bbmp.gov.in' },
  { code: 'BESCOM',      name: 'BESCOM',                 handle: '@bescomofficial',    email: 'helpdesk@bescom.co.in' },
  { code: 'BWSSB',       name: 'BWSSB',                  handle: '@bwssb_official',    email: 'comp@bwssb.gov.in' },
  { code: 'BMTC',        name: 'BMTC',                   handle: '@BMTC_BENGALURU',    email: 'mdbmtc@gmail.com' },
  { code: 'TRAFFIC',     name: 'Bangalore Traffic Police', handle: '@blrcitytraffic',  email: 'addlcptraffic-blr@ksp.gov.in' },
  { code: 'KSPCB',       name: 'KSPCB',                  handle: '',                   email: 'mail@kspcb.gov.in' },
  { code: 'BMRCL',       name: 'BMRCL · Metro',          handle: '@OfficialBMRCL',     email: 'info@bmrc.co.in' },
  { code: 'FOREST',      name: 'Karnataka Forest Dept',  handle: '@aranya_kfd',        email: '' }
];

// Issue → primary agency routing (from master doc)
export const ROUTING = {
  'Pothole':              'BBMP-ROADS',
  'Garbage':              'BBMP-SWM',
  'Streetlight':          'BBMP-ELEC',
  'Footpath':             'BBMP-ROADS',
  'Open drain':           'BWSSB',
  'Water leak':           'BWSSB',
  'Hanging wire':         'BESCOM',
  'Power outage':         'BESCOM',
  'Bus stop':             'BMTC',
  'Traffic signal':       'TRAFFIC',
  'Tree fall':            'FOREST',
  'Illegal construction': 'BBMP-ROADS'
};

const ISSUE_TYPES = Object.keys(ROUTING);

// Deterministic pseudo-random — keeps the demo identical across reloads.
function mulberry32(a) {
  return function() {
    let t = (a += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function seedComplaints(n = 200, salt = 1) {
  const rand = mulberry32(salt);
  const out = [];
  for (let i = 0; i < n; i++) {
    const ward = WARDS[Math.floor(rand() * WARDS.length)];
    const issue = ISSUE_TYPES[Math.floor(rand() * ISSUE_TYPES.length)];
    const dx = (rand() - 0.5) * 0.04;
    const dy = (rand() - 0.5) * 0.04;
    const ageDays = Math.floor(rand() * 60);
    const status = ageDays < 7 ? 'open'
                 : rand() < ward.resolution ? 'resolved'
                 : ageDays > 30 ? 'escalated' : 'open';
    out.push({
      id: `NMC-${1000 + i}`,
      issue,
      severity: 1 + Math.floor(rand() * 5),
      ward: ward.id,
      wardName: ward.name,
      ll: [ward.ll[0] + dx, ward.ll[1] + dy],
      agency: ROUTING[issue],
      ageDays,
      status,
      author: ['anon', 'Sneha R.', 'Rohit K.', 'M. Bhaskar', 'P. Iyer'][Math.floor(rand() * 5)]
    });
  }
  return out;
}

export const COMPLAINTS = seedComplaints(200, 1);

// Aggregate stats derived from the seed (so the dashboard "lives" off it)
export function aggregateStats(complaints = COMPLAINTS) {
  const total = complaints.length;
  const resolved = complaints.filter(c => c.status === 'resolved').length;
  const open = total - resolved;
  return {
    total,
    open,
    resolved,
    resolvedPct: Math.round((resolved / total) * 100),
    wardsReporting: new Set(complaints.map(c => c.ward)).size,
    medianFirstResponse: 7.2
  };
}

// Find nearby (≤500m approx — using degree distance for demo) within window.
export function findNearby(complaint, complaints = COMPLAINTS, radiusKm = 0.5, days = 30) {
  const KM_PER_DEG = 111;
  const matches = complaints.filter(c => {
    if (c.id === complaint.id) return false;
    if (c.issue !== complaint.issue) return false;
    if (c.ageDays > days) return false;
    const dLat = (c.ll[0] - complaint.ll[0]) * KM_PER_DEG;
    const dLon = (c.ll[1] - complaint.ll[1]) * KM_PER_DEG * Math.cos(complaint.ll[0] * Math.PI / 180);
    return Math.hypot(dLat, dLon) <= radiusKm;
  });
  return matches;
}

// Officer scorecards — derived from ward
export function officerForWard(wardId) {
  const ward = WARDS.find(w => w.id === wardId) || WARDS[0];
  return {
    name: ward.councillor,
    role: 'Ward Engineer',
    ward: ward.id,
    wardName: ward.name,
    zone: ward.id < 100 ? 'NW zone' : 'SE zone',
    handled: Math.round(ward.open * 1.2),
    avgResponse: ward.avg,
    resolutionRate: Math.round(ward.resolution * 100),
    since: 'Aug 2023'
  };
}
