import { Satellite, Anomaly, LogEntry, QuantumJob, SystemStatus, IngestionStream, CausalNode, IntelReport, TaskingRequest, LatentPoint, DataObject, TimeSeriesPoint, GravitySpectrum, NeuralModule, Qubit, ExplorationCampaign, CAMPAIGN_PHASES, Voxel, SeepageNode, PricingPackage, PricingAddOn, DrillRecord } from './types';

export { CAMPAIGN_PHASES };

export const GLOBAL_MINERAL_PROVINCES = [
    { name: 'Witwatersrand Basin', type: ['Gold', 'Uranium'], bounds: [-29, 26, -26, 29], desc: 'World\'s largest gold reserve.' },
    { name: 'Carlin Trend', type: ['Gold'], bounds: [40, -117, 41, -116], desc: 'Sediment-hosted disseminated gold (Nevada).' },
    { name: 'Lithium Triangle', type: ['Lithium', 'Potash'], bounds: [-26, -69, -18, -66], desc: 'High-altitude salar brines (Chile/Arg/Bolivia).' },
    { name: 'Bushveld Complex', type: ['PGM', 'Chrome'], bounds: [-26, 26, -24, 31], desc: 'Largest layered igneous intrusion.' }
];

export const ACTIVE_CAMPAIGN: ExplorationCampaign = {
  id: 'CMP-2023-9981',
  name: 'Project Rift Valley: Strategic Gas & Critical Minerals',
  targetCoordinates: '8.12° S, 33.45° E',
  regionName: 'Tanzania / Mozambique Belt',
  resourceType: 'Multi-Objective',
  targetElement: 'He, REE, H2',
  targets: [
    { resourceType: 'Noble Gas', targetElement: 'He' },
    { resourceType: 'Rare Earth Elements', targetElement: 'NdPr' },
    { resourceType: 'Future Energy', targetElement: 'H2 (Natural)' }
  ],
  results: [
    {
        element: 'He',
        resourceType: 'Noble Gas',
        status: 'Confirmed',
        probability: 0.94,
        specifications: { grade: 10.5, tonnage: 135000, depth: 1200, purity: 98.5 }
    },
    {
        element: 'NdPr',
        resourceType: 'Rare Earth Elements',
        status: 'Confirmed',
        probability: 0.88,
        specifications: { grade: 4.2, tonnage: 8.5, depth: 150, purity: 92.0 }
    }
  ],
  drillTargets: [],
  environment: 'Land',
  radius: 120,
  dataVolumeEstimate: 5.2,
  currentPhase: CAMPAIGN_PHASES[0],
  phaseIndex: 0,
  phaseProgress: 25,
  startDate: '2023-10-25',
  estimatedCompletion: '2023-11-05',
  accuracyScore: 0.25,
  status: 'Active',
  iteration: 1,
  priorsLoaded: true
};

export const RESOURCE_CATALOG = [
  // GOLD SYSTEM
  { category: 'Arsenopyrite', group: 'Gold', default: 'Au', primaryMethod: 'SWIR 0.55µm', maxDepth: '900m' },
  { category: 'Pyrite', group: 'Gold', default: 'Au', primaryMethod: 'VNIR 0.89µm', maxDepth: '1.2km' },
  { category: 'Scorodite', group: 'Gold', default: 'As/Au', primaryMethod: 'VNIR 0.45µm', maxDepth: '50m' },
  
  // COPPER SYSTEM
  { category: 'Chalcopyrite', group: 'Copper', default: 'Cu', primaryMethod: 'VNIR 0.57µm', maxDepth: '2.5km' },
  { category: 'Bornite', group: 'Copper', default: 'Cu', primaryMethod: 'SWIR 1.15µm', maxDepth: '1.5km' },
  { category: 'Chalcocite', group: 'Copper', default: 'Cu', primaryMethod: 'SWIR 1.45µm', maxDepth: '1.2km' },
  { category: 'Covellite', group: 'Copper', default: 'Cu', primaryMethod: 'SWIR 1.35µm', maxDepth: '1.0km' },
  { category: 'Malachite', group: 'Copper', default: 'Cu', primaryMethod: 'SWIR 2.25µm', maxDepth: '50m' },
  { category: 'Azurite', group: 'Copper', default: 'Cu', primaryMethod: 'SWIR 2.50µm', maxDepth: '50m' },

  // LITHIUM SYSTEM
  { category: 'Spodumene', group: 'Lithium', default: 'Li', primaryMethod: 'SWIR 2.35µm', maxDepth: '1km' },
  { category: 'Lepidolite', group: 'Lithium', default: 'Li', primaryMethod: 'SWIR 2.20µm', maxDepth: '500m' },
  { category: 'Petalite', group: 'Lithium', default: 'Li', primaryMethod: 'SWIR 2.40µm', maxDepth: '800m' },
  { category: 'Amblygonite', group: 'Lithium', default: 'Li', primaryMethod: 'SWIR 2.45µm', maxDepth: '600m' },

  // ZINC / LEAD
  { category: 'Sphalerite', group: 'Zinc', default: 'Zn', primaryMethod: 'SWIR 1.75µm', maxDepth: '1.2km' },
  { category: 'Galena', group: 'Lead', default: 'Pb', primaryMethod: 'VNIR 0.65µm', maxDepth: '1.5km' },
  { category: 'Smithsonite', group: 'Zinc', default: 'Zn', primaryMethod: 'SWIR 2.30µm', maxDepth: '200m' },
  { category: 'Hemimorphite', group: 'Zinc', default: 'Zn', primaryMethod: 'SWIR 1.90µm', maxDepth: '300m' },
  { category: 'Hydrozincite', group: 'Zinc', default: 'Zn', primaryMethod: 'SWIR 2.35µm', maxDepth: '150m' },

  // NICKEL / COBALT
  { category: 'Pentlandite', group: 'Nickel', default: 'Ni', primaryMethod: 'VNIR 0.95µm', maxDepth: '2km' },
  { category: 'Garnierite', group: 'Nickel', default: 'Ni', primaryMethod: 'SWIR 2.20µm', maxDepth: '400m' },
  { category: 'Violarite', group: 'Nickel', default: 'Ni', primaryMethod: 'VNIR 1.00µm', maxDepth: '600m' },
  { category: 'Cobaltite', group: 'Cobalt', default: 'Co', primaryMethod: 'SWIR 1.50µm', maxDepth: '1km' },

  // STRATEGIC / REE
  { category: 'Bastnäsite', group: 'REE', default: 'Ce', primaryMethod: 'SWIR 2.00µm', maxDepth: '150m' },
  { category: 'Monazite', group: 'REE', default: 'Ce', primaryMethod: 'SWIR 2.20µm', maxDepth: '200m' },
  { category: 'Xenotime', group: 'REE', default: 'Y', primaryMethod: 'SWIR 2.30µm', maxDepth: '250m' },

  // IRON SYSTEM
  { category: 'Hematite', group: 'Iron', default: 'Fe', primaryMethod: 'VNIR 0.86µm', maxDepth: '500m' },
  { category: 'Magnetite', group: 'Iron', default: 'Fe', primaryMethod: 'VNIR 1.15µm', maxDepth: '1km' },
  { category: 'Goethite', group: 'Iron', default: 'Fe', primaryMethod: 'VNIR 0.92µm', maxDepth: '400m' },

  // ALTERATION / PATHFINDERS
  { category: 'Kaolinite', group: 'Alteration', default: 'Al-OH', primaryMethod: 'SWIR 2.21µm', maxDepth: '100m' },
  { category: 'Alunite', group: 'Alteration', default: 'K-Al', primaryMethod: 'SWIR 1.76µm', maxDepth: '200m' },
  { category: 'Jarosite', group: 'Alteration', default: 'Fe-OH', primaryMethod: 'VNIR 0.43µm', maxDepth: '150m' },
  { category: 'Muscovite', group: 'Alteration', default: 'K-mica', primaryMethod: 'SWIR 2.20µm', maxDepth: '1km' },
  { category: 'Chlorite', group: 'Alteration', default: 'Mg-Fe', primaryMethod: 'SWIR 2.25µm', maxDepth: '1.5km' },
  { category: 'Epidote', group: 'Alteration', default: 'Ca-Al', primaryMethod: 'SWIR 2.34µm', maxDepth: '1.2km' },

  // ADDITIONAL STRATEGIC
  { category: 'Scheelite', group: 'Strategic', default: 'W', primaryMethod: 'SWIR 1.95µm', maxDepth: '800m' },
  { category: 'Wolframite', group: 'Strategic', default: 'W', primaryMethod: 'VNIR 0.65µm', maxDepth: '900m' },
  { category: 'Molybdenite', group: 'Strategic', default: 'Mo', primaryMethod: 'VNIR 0.70µm', maxDepth: '3km' }
];

export const SATELLITES: Satellite[] = [
  { id: 'sat-1', name: 'Sentinel-1A', type: 'SAR', orbit: 'LEO', status: SystemStatus.ONLINE, lastPass: '10m ago', coverage: 98 },
  { id: 'sat-2', name: 'Landsat 9', type: 'Hyperspectral', orbit: 'LEO', status: SystemStatus.PROCESSING, lastPass: '45m ago', coverage: 92 },
  { id: 'sat-3', name: 'GOCE-2', type: 'Gravimetric', orbit: 'LEO', status: SystemStatus.ONLINE, lastPass: '2h ago', coverage: 100 }
];

export const ANOMALIES: Anomaly[] = [
  { id: 'anom-1', coordinates: [-8.12, 33.45], depth: 1200, probability: 0.94, type: 'Helium Reservoir', description: 'Fault-controlled seep.', physicsResidual: 0.001, status: 'Confirmed' }
];

export const MOCK_LOGS: LogEntry[] = [
  { id: 'log-1', timestamp: '10:42:05', subsystem: 'PCFC', message: 'Physics constraint converged.', level: 'SUCCESS' }
];

export const QUANTUM_JOBS: QuantumJob[] = [
  { id: 'QJ-8821', targetRegion: 'Tanzania Rift', qubitsUsed: 128, status: 'Running', progress: 45 }
];

export const MOCK_QUBITS: Qubit[] = Array.from({ length: 64 }, (_, i) => ({
  id: `q-${i}`, row: Math.floor(i / 8), col: i % 8, coherenceTime: 142, gateFidelity: 0.999, status: 'Active'
}));

export const INGESTION_STREAMS: IngestionStream[] = [
  { id: 'pipe-01', source: 'Sentinel-1', type: 'SAR', throughput: 1.2, status: SystemStatus.ONLINE, domain: 'Land', stages: [] },
  { id: 'pipe-02', source: 'Landsat 9', type: 'Optical', throughput: 0.8, status: SystemStatus.ONLINE, domain: 'Land', stages: [] }
];

export const CAUSAL_NODES: CausalNode[] = [
  { id: 'n1', label: 'Surface Deformation', type: 'observable', confidence: 0.95, parents: ['n4'], x: 400, y: 50 },
  { id: 'n8', label: 'Poisson Equation', type: 'physics', confidence: 1.0, parents: [], x: 400, y: 500 }
];

export const SEEPAGE_NETWORK: SeepageNode[] = [
    { id: 's1', label: 'Deep Source', type: 'Source', depth: 4500, pressure: 95, probability: 0.9, x: 100, y: 350, next: ['o1'] },
    { id: 'o1', label: 'Soil Gas', type: 'Seep', depth: 0, pressure: 1, probability: 0.95, x: 700, y: 50, next: [] }
];

export const NEURAL_MODULES: NeuralModule[] = [
  { id: 'm1', name: 'SpectralNet-v4', architecture: 'Transformer', function: 'Alignment', inputShape: '(13, 256, 256)', status: 'Converged', loss: 0.0023, accuracy: 0.992 }
];

export const INTEL_REPORTS: IntelReport[] = [
  { id: 'RPT-001', title: 'Helium Discovery', date: '2023-10-12', region: 'Tanzania', priority: 'High', summary: 'Major accumulation identified.', tags: ['Helium'], status: 'Published' }
];

export const TASKING_REQUESTS: TaskingRequest[] = [
  { id: 'TSK-9921', targetCoordinates: '8.12 S, 33.45 E', sensorType: 'SAR', priority: 'Urgent', status: 'Pending', requestor: 'Ops', submittedAt: '10m ago' }
];

export const DATA_LAKE_FILES: DataObject[] = [
  { id: 'obj-1', name: 'S1A_RAW_DATA.zip', bucket: 'Raw', size: '1.2 GB', type: 'SAR', lastModified: '2023-10-12', owner: 'Ingest' }
];

export const TEMPORAL_DATA: TimeSeriesPoint[] = [
  { date: 'Jan', deformation: 2, thermalInertia: 850, coherence: 0.9 }
];

export const GRAVITY_SPECTRUM: GravitySpectrum[] = [
  { wavelength: 'Short (Shallow)', power: 120, depthEstimate: '< 2km' }
];

export const LICENSING_PACKAGES: PricingPackage[] = [
  { id: 'pkg-1', name: 'National Twin', scope: 'Country-wide', features: ['National Mapping'], priceMin: 2.5e6, priceMax: 6.0e6, unit: 'project' }
];

export const COMMERCIAL_ADDONS: PricingAddOn[] = [
  { id: 'add-1', name: 'Custom Investor Report', price: 50000, unit: 'flat', type: 'Add-On', description: 'Executive slide deck.' }
];

export const DRILL_HOLE_DATABASE: Record<string, DrillRecord[]> = {
    'tz': [{ id: 'W-01', lat: -8.12, lon: 33.45, depth_m: 1200, measurement_value: 10.2, measurement_unit: 'He %', lithology: 'Sandstone', sample_date: '2023-01-01', source: 'TGS', license: 'Public', notes: '' }]
};

export const MOCK_VOXELS: Voxel[] = Array.from({length: 64}, (_, i) => ({
    id: `v-${i}`, x: i%4, y: Math.floor((i%16)/4), z: Math.floor(i/16), lithology: 'Sandstone', density: 2.35, mineralProb: 0.85, uncertainty: 0.1
}));
