import { ExplorationCampaign, SystemStatus, ConnectivityResult, DiscoveryRecord, MineralAgentType, TargetResult, DrillTarget, IntelReport } from './types';
import { ACTIVE_CAMPAIGN } from './constants';
import { APP_CONFIG } from './config';

const STORAGE_KEYS = {
  BACKEND_OVERRIDE: 'aurora_live_backend_url'
};

// Fix: Define JobStatus interface for internal API usage
export interface JobStatus {
  job_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress: number;
  current_task: string;
}

export class AuroraAPI {
  private static baseUrl = '';
  private static isBackendOnline = false;
  private static serverStatus: any = null;
  private static overrideFailed = false; // Track if manual override fails

  private static getBaseUrl(): string {
      // Priority 1: Respect localStorage override if user manually set it AND it hasn't failed
      const override = localStorage.getItem(STORAGE_KEYS.BACKEND_OVERRIDE);
      if (override && override.trim() && !this.overrideFailed) {
        let trimmedOverride = override.trim().replace(/\/+$/, '');
        
        // Validate override format - must have protocol
        if (!trimmedOverride.startsWith('http://') && !trimmedOverride.startsWith('https://')) {
          console.warn(`⚠️ Invalid override format (missing http:// or https://): ${trimmedOverride} - clearing it`);
          localStorage.removeItem(STORAGE_KEYS.BACKEND_OVERRIDE);
          // Fall through to auto-detection
        } else if (typeof window !== 'undefined') {
          const hostname = window.location.hostname;
          const isProduction = !hostname.includes('localhost') && !hostname.includes('127.0.0.1');
          const isLocalhostUrl = trimmedOverride.includes('localhost') || trimmedOverride.includes('127.0.0.1');
          
          if (isProduction && isLocalhostUrl) {
            console.warn(`⚠️  Manual override (${trimmedOverride}) is for localhost but running on production (${hostname}) - clearing it`);
            localStorage.removeItem(STORAGE_KEYS.BACKEND_OVERRIDE);
            this.overrideFailed = true;
            // Fall through to auto-detection
          } else {
            // On production, append /api if not already there
            if (isProduction && !trimmedOverride.includes('/api')) {
              trimmedOverride = trimmedOverride + '/api';
            }
            console.log(`📍 Using manual backend override: ${trimmedOverride}`);
            return trimmedOverride;
          }
        } else {
          console.log(`📍 Using manual backend override: ${trimmedOverride}`);
          return trimmedOverride;
        }
      }
      
      // Priority 2: Auto-detect based on environment
      if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        
        // On Railway or any production (non-localhost):
        // Backend runs in same container, accessed via Express proxy at /api
        if (!hostname.includes('localhost') && !hostname.includes('127.0.0.1')) {
          console.log(`🚀 Production environment detected (${hostname}): using /api proxy`);
          return '/api';
        }
        
        // On localhost: Backend is separate process on port 8000
        console.log(`💻 Local development detected: using direct backend URL`);
        return 'http://localhost:8000';
      }
      
      // Fallback (shouldn't reach here in browser)
      return 'http://localhost:8000';
  }

  /**
   * Initializes connection with the Railway/Neon stack.
   * Includes retry logic for backend startup delays.
   */
  static async init(): Promise<boolean> {
    this.baseUrl = this.getBaseUrl();
    console.log(`📡 Initializing Aurora API with base URL: ${this.baseUrl}`);
    
    // Retry logic: try up to 3 times with delays
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const health = await this.checkConnectivity();
        this.isBackendOnline = health.status !== SystemStatus.OFFLINE;
        if (this.isBackendOnline) {
          console.log(`✅ Backend online (attempt ${attempt}/3)`);
          return true;
        }
      } catch (e) {
        console.warn(`⚠️ Connectivity check failed (attempt ${attempt}/3): ${(e as Error).message}`);
      }
      
      // Wait before next attempt (except on last attempt)
      if (attempt < 3) {
        await new Promise(r => setTimeout(r, 2000 * attempt)); // 2s, 4s delays
      }
    }
    
    console.warn(`❌ Backend still unreachable after 3 attempts. Will retry in App.tsx startup.`);
    this.isBackendOnline = false;
    return false;
  }

  static getActiveEndpoint = () => this.getBaseUrl();
  
  static setBackendUrl(url: string) {
      if (!url || url.trim() === '') {
          localStorage.removeItem(STORAGE_KEYS.BACKEND_OVERRIDE);
          this.overrideFailed = false;
      } else {
          localStorage.setItem(STORAGE_KEYS.BACKEND_OVERRIDE, url.trim());
          this.overrideFailed = false; // Reset flag when user sets new URL
      }
      this.baseUrl = this.getBaseUrl();
  }
  
  static async checkConnectivity(): Promise<ConnectivityResult> {
    const url = this.getBaseUrl();
    const endpoints = ['/system/health', '/health', '/'];
    
    for (const endpoint of endpoints) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout for production proxy
            
            const res = await fetch(`${url}${endpoint}`, { 
                signal: controller.signal,
                headers: { 'Accept': 'application/json' },
                cache: 'no-cache'
            });
            clearTimeout(timeoutId);
            
            if (res.ok) {
                try {
                    const data = await res.json();
                    this.serverStatus = data;
                    console.log(`✅ Backend health check successful: ${endpoint}`, data);
                } catch (e) {
                    this.serverStatus = { status: 'operational' }; 
                }
                
                return { 
                    status: SystemStatus.ONLINE, 
                    mode: 'Cloud',
                    message: 'LIVE_UPLINK_STABLE'
                };
            }
        } catch (e) {
            console.warn(`⚠️ Health check failed for endpoint ${endpoint}:`, (e as Error).message);
            continue;
        }
    }
    
    console.warn(`❌ All backend endpoints unreachable from ${url}`);
    return { status: SystemStatus.OFFLINE, mode: 'Sovereign', message: 'Stack Unreachable' };
  }

  static isNeonActive = () => {
      if (!this.serverStatus) return false;
      const status = String(this.serverStatus.database || this.serverStatus.db || 'CONNECTED').toUpperCase();
      return ['CONNECTED', 'READY', 'OK', 'ACTIVE', 'OPERATIONAL'].includes(status);
  };

  static isGeePersistent = () => {
      if (!this.serverStatus) return false;
      const status = String(this.serverStatus.gee || this.serverStatus.spectral || 'INITIALIZED').toUpperCase();
      return ['INITIALIZED', 'READY', 'OK', 'ACTIVE', 'OPERATIONAL'].includes(status);
  };

  private static async apiFetch(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = this.getBaseUrl();
    const cleanPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const fullUrl = `${url}${cleanPath}`;
    
    // Log the full URL being called (for debugging)
    if (endpoint.includes('scans') || endpoint.includes('seismic')) {
      console.log(`📡 API Call: ${fullUrl}`);
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const res = await fetch(fullUrl, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });
      clearTimeout(timeoutId);
      
      if (!res.ok) {
        console.warn(`API ${res.status} for ${cleanPath}`);
        throw new Error(`API Error: ${res.status}`);
      }
      return res.json();
    } catch (err: any) {
      console.warn(`API fetch failed for ${cleanPath}: ${err.message}`);
      throw err;
    }
  }

  static async launchRealMission(payload: any): Promise<any> {
    return this.apiFetch('/scans', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static async listScans(limit: number = 100, offset: number = 0): Promise<any> {
    try {
      return await this.apiFetch(`/scans?limit=${limit}&offset=${offset}`);
    } catch(e) {
      return { total: 0, scans: [], limit, offset };
    }
  }

  static async getMissionStatus(missionId: string): Promise<any> {
    return this.apiFetch(`/scans/${missionId}`);
  }

  // Fix: Implement missing getJobStatus used in App.tsx
  static async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.apiFetch(`/jobs/${jobId}/status`);
  }

  // Fix: Implement missing getJobResults used in App.tsx
  static async getJobResults(jobId: string): Promise<{ results: TargetResult[], drillTargets: DrillTarget[] }> {
    return this.apiFetch(`/jobs/${jobId}/artifacts/results.json`);
  }

  static async getActiveCampaign(): Promise<ExplorationCampaign> {
    const url = this.getBaseUrl();
    try {
        const res = await fetch(`${url}/scans`);
        if (res.ok) {
            const scans = await res.json();
            const active = Array.isArray(scans) ? scans.find((s: any) => s.status === 'active') : null;
            if (active) {
                return {
                    id: active.scan_id || active.id,
                    name: active.name || 'Active Scan',
                    targetCoordinates: active.aoi || '',
                    regionName: active.region || '',
                    resourceType: active.minerals?.[0] || '',
                    targetElement: active.minerals?.[0] || '',
                    targets: [],
                    results: [],
                    drillTargets: [],
                    radius: active.radius_km || 50,
                    dataVolumeEstimate: 0,
                    currentPhase: 'Acquisition',
                    phaseIndex: 0,
                    phaseProgress: active.progress || 0,
                    startDate: new Date().toISOString(),
                    accuracyScore: 0.85,
                    status: 'Active',
                    iteration: 1,
                    priorsLoaded: false,
                    autoPlay: false
                };
            }
        }
    } catch(e) {}
    return ACTIVE_CAMPAIGN;
  }

  static async updateCampaign(campaign: ExplorationCampaign): Promise<void> {
    // Campaigns are tracked via scans endpoint, update is local-only in Sovereign mode
    return Promise.resolve();
  }

  static async getAllCampaigns(): Promise<ExplorationCampaign[]> {
    const url = this.getBaseUrl();
    try {
        const res = await fetch(`${url}/scans`);
        if (res.ok) {
            const scans = await res.json();
            return Array.isArray(scans) ? scans.map((s: any) => ({
                id: s.scan_id || s.id,
                name: s.name || 'Scan',
                targetCoordinates: s.aoi || '',
                regionName: s.region || '',
                resourceType: s.minerals?.[0] || '',
                targetElement: s.minerals?.[0] || '',
                targets: [],
                results: [],
                drillTargets: [],
                radius: s.radius_km || 50,
                dataVolumeEstimate: 0,
                currentPhase: 'Acquisition',
                phaseIndex: 0,
                phaseProgress: s.progress || 0,
                startDate: new Date().toISOString(),
                accuracyScore: 0.85,
                status: (s.status === 'active' ? 'Active' : s.status === 'completed' ? 'Completed' : 'Paused') as 'Active' | 'Completed' | 'Paused',
                iteration: 1,
                priorsLoaded: false,
                autoPlay: false
            })) : [ACTIVE_CAMPAIGN];
        }
    } catch(e) {}
    return [ACTIVE_CAMPAIGN];
  }

  static async getGlobalDiscoveries(): Promise<DiscoveryRecord[]> {
    const url = this.getBaseUrl();
    try {
        const res = await fetch(`${url}/discoveries/global`);
        if (res.ok) return await res.json();
    } catch(e) {}
    return [];
  }

  static async generateAndSaveReport(campaign: ExplorationCampaign): Promise<IntelReport> {
    // In Sovereign mode, generate a local report
    // In connected mode, would fetch from /scans/{id}/report
    try {
        return await this.apiFetch(`/scans/${campaign.jobId}/report`);
    } catch(e) {
        // Fallback: generate local report in Sovereign mode
        return {
            id: campaign.jobId || 'report-local',
            title: `Spectral Analysis Report`,
            date: new Date().toISOString(),
            region: campaign.regionName || campaign.targetCoordinates,
            priority: 'High',
            summary: `Spectral analysis complete for ${campaign.regionName || campaign.targetCoordinates}`,
            tags: campaign.targets.map(t => t.resourceType),
            status: 'Published'
        };
    }
  }

  // Data Lake View Methods
  static async getDataLakeFiles(): Promise<any[]> {
    try {
      return await this.apiFetch('/data-lake/files');
    } catch(e) {
      return [
        { id: 'obj-1', name: 'S1A_RAW_DATA.zip', bucket: 'Raw', size: '1.2 GB', type: 'SAR', lastModified: '2023-10-12', owner: 'Ingest' },
        { id: 'obj-2', name: 'L8_PROCESSED.tif', bucket: 'Processed', size: '450 MB', type: 'Multispectral', lastModified: '2023-10-15', owner: 'Processing' }
      ];
    }
  }

  static async getDataLakeStats(): Promise<any> {
    try {
      return await this.apiFetch('/data-lake/stats');
    } catch(e) {
      return { totalObjects: 1250, totalSize: '125 TB', buckets: 4, lastIngestion: new Date().toISOString() };
    }
  }

  static async generateFileContent(fileName: string, fileType: string): Promise<string> {
    try {
      return await this.apiFetch(`/data-lake/files/${fileName}/content?type=${fileType}`);
    } catch(e) {
      return `Content for file ${fileName}`;
    }
  }

  static async processFile(fileId: string, processType: string): Promise<any> {
    try {
      return await this.apiFetch(`/data-lake/files/${fileId}/process`, { method: 'POST', body: JSON.stringify({ processType }) });
    } catch(e) {
      return { id: fileId, status: 'processing', progress: 0, processType };
    }
  }

  // Digital Twin View Methods
  static async getDigitalTwinVoxels(lat: number, lon: number): Promise<any> {
    try {
      return await this.apiFetch(`/twin/voxels?lat=${lat}&lon=${lon}`);
    } catch(e) {
      return { voxels: [] };
    }
  }

  // IETL View Methods
  static async getReports(): Promise<any[]> {
    try {
      return await this.apiFetch('/ietl/reports');
    } catch(e) {
      return [
        { id: 'rep-1', title: 'Weekly Ingestion Summary', date: new Date().toISOString(), status: 'Completed' },
        { id: 'rep-2', title: 'Data Quality Assessment', date: new Date(Date.now() - 86400000).toISOString(), status: 'Completed' }
      ];
    }
  }

  static async getTasks(): Promise<any[]> {
    try {
      return await this.apiFetch('/ietl/tasks');
    } catch(e) {
      return [
        { id: 'tsk-1', name: 'Sentinel-2 Download', status: 'running', progress: 45 },
        { id: 'tsk-2', name: 'SAR Harmonization', status: 'queued', progress: 0 }
      ];
    }
  }

  // OSIL View Methods
  static async getSatelliteSchedule(lat: number, lon: number): Promise<any> {
    try {
      return await this.apiFetch(`/osil/schedule?lat=${lat}&lon=${lon}`);
    } catch(e) {
      return { schedule: [
        { id: 'TSK-9920', satellite: 'Sentinel-1', targetCoordinates: `${lat}, ${lon}`, sensorType: 'SAR', priority: 'High', status: 'Scheduled', requestor: 'Ops', submittedAt: '2h ago' },
        { id: 'TSK-9921', satellite: 'Sentinel-2', targetCoordinates: `${lat}, ${lon}`, sensorType: 'Multispectral', priority: 'Urgent', status: 'Pending', requestor: 'Ops', submittedAt: '10m ago' }
      ]};
    }
  }

  static async submitTask(task: any): Promise<any> {
    try {
      return await this.apiFetch('/osil/task', { method: 'POST', body: JSON.stringify(task) });
    } catch(e) {
      return { id: `TSK-${Date.now()}`, status: 'Pending' };
    }
  }

  // PCFC View Methods
  static async runPhysicsInversion(lat: number, lon: number, depth: number): Promise<any> {
    try {
      return await this.apiFetch('/physics/invert', { method: 'POST', body: JSON.stringify({ lat, lon, depth }) });
    } catch(e) {
      return { jobId: `PHYS-${Date.now()}`, status: 'queued', residuals: [], structure: {} };
    }
  }

  static async getPhysicsTomography(lat: number, lon: number): Promise<any> {
    try {
      return await this.apiFetch(`/physics/tomography/${lat}/${lon}`);
    } catch(e) {
      return { slice: [], residuals: [], structure: {} };
    }
  }

  // Portfolio View Methods
  static async getPortfolioOverview(): Promise<any> {
    try {
      return await this.apiFetch('/portfolio/overview');
    } catch(e) {
      // Return mock portfolio data matching PortfolioSummary structure
      return {
        summary: {
          total_npv_usd: 2300000000,
          asset_count: 42,
          total_diesel_saved_l: 1200000,
          total_water_saved_m3: 450000
        },
        assets: [
          {
            id: 'AST-001',
            name: 'Bolivian Lithium Prospect',
            type: 'Mineral Exploration',
            status: {
              lifecycle_stage: 'advanced_exploration',
              risk_profile: 'Medium'
            },
            economics: {
              npv_usd: 450000000,
              roi_percent: 28.5,
              gross_value_usd: 1200000000
            },
            esg: {
              carbon_intensity: 12.5
            }
          },
          {
            id: 'AST-002',
            name: 'North Sea Gas Field',
            type: 'Oil & Gas',
            status: {
              lifecycle_stage: 'production',
              risk_profile: 'Low'
            },
            economics: {
              npv_usd: 780000000,
              roi_percent: 42.1,
              gross_value_usd: 1850000000
            },
            esg: {
              carbon_intensity: 28.3
            }
          },
          {
            id: 'AST-003',
            name: 'Rare Earth Elements Project',
            type: 'Mineral Exploration',
            status: {
              lifecycle_stage: 'prefeasibility',
              risk_profile: 'High'
            },
            economics: {
              npv_usd: 650000000,
              roi_percent: 65.2,
              gross_value_usd: 1500000000
            },
            esg: {
              carbon_intensity: 19.8
            }
          }
        ]
      };
    }
  }

  // QSE View Methods
  static async runQuantumOptimization(lat: number, lon: number, depth: number): Promise<any> {
    try {
      return await this.apiFetch('/quantum/optimize', { method: 'POST', body: JSON.stringify({ lat, lon, depth }) });
    } catch(e) {
      return { jobId: `QNT-${Date.now()}`, status: 'queued', optimizationScore: 0.92 };
    }
  }

  // Seismic View Methods
  static async getSeismicSlice(lat: number, lon: number, index: number, axis: string): Promise<any> {
    try {
      return await this.apiFetch(`/seismic/${lat}/${lon}/${axis}/${index}`);
    } catch(e) {
      return { width: 512, height: 512, data: Array(512).fill(Array(512).fill(0)), uncertainty: Array(512).fill(Array(512).fill(0)), horizons: [], faults: [] };
    }
  }

  static async getStructuralTraps(lat: number, lon: number): Promise<any[]> {
    try {
      return await this.apiFetch(`/seismic/${lat}/${lon}/traps`);
    } catch(e) {
      return [
        { id: 'trap-1', name: 'Anticlinal Closure', type: 'Structural', confidence: 0.87, volumetrics: 125, coordinates: { x: 250, y: 150, z: 2500 } },
        { id: 'trap-2', name: 'Fault-Seal System', type: 'Structural', confidence: 0.72, volumetrics: 87, coordinates: { x: 350, y: 280, z: 3100 } }
      ];
    }
  }

  static async startSeismicJob(campaignId: string): Promise<any> {
    try {
      return await this.apiFetch('/seismic/job', { method: 'POST', body: JSON.stringify({ campaignId }) });
    } catch(e) {
      return { jobId: `SEIS-${Date.now()}`, status: 'Ingesting', progress: 0, currentTask: 'Initializing...' };
    }
  }

  // TMAL View Methods
  static async getTemporalAnalysis(lat: number, lon: number): Promise<any> {
    try {
      return await this.apiFetch(`/temporal/${lat}/${lon}`);
    } catch(e) {
      return {
        timeSeries: [
          { date: 'Jan', deformation: 2, thermalInertia: 850, coherence: 0.9 },
          { date: 'Feb', deformation: 2.5, thermalInertia: 860, coherence: 0.88 }
        ],
        trends: []
      };
    }
  }

  // Satellite Data Methods
  static async fetchSatelliteData(latitude: number, longitude: number, dateStart?: string, dateEnd?: string): Promise<any> {
    try {
      const body = {
        latitude,
        longitude,
        date_start: dateStart || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        date_end: dateEnd || new Date().toISOString().split('T')[0]
      };
      return await this.apiFetch('/satellite-data', { method: 'POST', body: JSON.stringify(body) });
    } catch(e) {
      // Demo fallback: Sentinel-2 L2A data
      return {
        source: 'Sentinel-2',
        level: 'L2A',
        acquisition_date: new Date().toISOString().split('T')[0],
        bands: [
          { band: 'B2', wavelength: 490, resolution: 10, values: Array(100).fill(0.15) },
          { band: 'B3', wavelength: 560, resolution: 10, values: Array(100).fill(0.18) },
          { band: 'B4', wavelength: 665, resolution: 10, values: Array(100).fill(0.12) },
          { band: 'B5', wavelength: 705, resolution: 20, values: Array(100).fill(0.22) },
          { band: 'B6', wavelength: 740, resolution: 20, values: Array(100).fill(0.25) },
          { band: 'B7', wavelength: 783, resolution: 20, values: Array(100).fill(0.28) },
          { band: 'B8', wavelength: 842, resolution: 10, values: Array(100).fill(0.35) },
          { band: 'B11', wavelength: 1610, resolution: 20, values: Array(100).fill(0.15) },
          { band: 'B12', wavelength: 2190, resolution: 20, values: Array(100).fill(0.08) }
        ],
        indices: {
          ndvi: Array(100).fill(0.42),
          ndbi: Array(100).fill(0.18)
        },
        cloud_cover: 5.2,
        mgrs_tile: '36SWB',
        orbital_number: 134
      };
    }
  }

  static async analyzeSpectralData(satelliteData?: any): Promise<any> {
    try {
      const body = satelliteData || {};
      return await this.apiFetch('/analyze-spectra', { method: 'POST', body: JSON.stringify(body) });
    } catch(e) {
      // Demo fallback: Mineral detections
      return {
        detections: [
          {
            mineral: 'Copper',
            confidence: 0.92,
            location: { lat: -9.5, lon: 27.8 },
            area_km2: 2.3,
            wavelength_features: [705, 783, 842]
          },
          {
            mineral: 'Gold',
            confidence: 0.87,
            location: { lat: -9.48, lon: 27.82 },
            area_km2: 1.8,
            wavelength_features: [560, 665, 740]
          },
          {
            mineral: 'Cobalt',
            confidence: 0.82,
            location: { lat: -9.52, lon: 27.75 },
            area_km2: 1.5,
            wavelength_features: [490, 705, 1610]
          }
        ],
        analysis_timestamp: new Date().toISOString(),
        data_source: 'Sentinel-2 L2A',
        processing_level: 'Standard'
      };
    }
  }

  // Workflow API Methods - NO MOCK DATA
  static async runPINNAnalysis(lat: number, lon: number, satelliteData?: any): Promise<any> {
    try {
      return await this.apiFetch('/pinn/analyze', {
        method: 'POST',
        body: JSON.stringify({ latitude: lat, longitude: lon, satellite_data: satelliteData })
      });
    } catch (e) {
      return { error: 'PINN analysis failed - real data or processing unavailable', code: 'PINN_ERROR' };
    }
  }

  static async runUSHEAnalysis(spectralData: any): Promise<any> {
    try {
      return await this.apiFetch('/ushe/analyze', {
        method: 'POST',
        body: JSON.stringify({ spectral_data: spectralData })
      });
    } catch (e) {
      return { error: 'USHE harmonization failed - real data unavailable', code: 'USHE_ERROR' };
    }
  }

  static async runTMALAnalysis(lat: number, lon: number): Promise<any> {
    try {
      return await this.apiFetch('/tmal/analyze', {
        method: 'POST',
        body: JSON.stringify({ latitude: lat, longitude: lon })
      });
    } catch (e) {
      return { error: 'TMAL temporal analysis failed - real data unavailable', code: 'TMAL_ERROR' };
    }
  }

  static async generateVisualizations(analysisData: {
    satellite?: any;
    spectral?: any;
    pinn?: any;
    ushe?: any;
    tmal?: any;
  }): Promise<any> {
    try {
      return await this.apiFetch('/visualizations/generate', {
        method: 'POST',
        body: JSON.stringify(analysisData)
      });
    } catch (e) {
      return { error: 'Visualization generation failed', code: 'VIZ_ERROR' };
    }
  }

  static async storeScanResults(scanData: any): Promise<any> {
    try {
      return await this.apiFetch('/scans/store', {
        method: 'POST',
        body: JSON.stringify(scanData)
      });
    } catch (e) {
      return { error: 'Failed to store scan results in database', code: 'STORAGE_ERROR' };
    }
  }

  static async getAllScans(): Promise<any[]> {
    try {
      return await this.apiFetch('/scans/history');
    } catch (e) {
      console.error('Failed to fetch scan history:', e);
      return [];
    }
  }

  static async getScanDetails(scanId: string): Promise<any> {
    try {
      return await this.apiFetch(`/scans/${scanId}/details`);
    } catch (e) {
      return { error: 'Scan details not found', code: 'NOT_FOUND' };
    }
  }

  static async fetchRealSpectralData(aoi: any, mineral?: string): Promise<any> {
    try {
      return await this.apiFetch('/spectral/real', {
        method: 'POST',
        body: JSON.stringify({ aoi, target_mineral: mineral })
      });
    } catch (e) {
      return { error: 'Real spectral data unavailable', code: 'NO_DATA' };
    }
  }
}