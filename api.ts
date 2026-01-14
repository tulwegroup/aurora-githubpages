import { ExplorationCampaign, SystemStatus, ConnectivityResult, DiscoveryRecord, TaskingRequest, LatentPoint, DataObject, SeismicSlice, SeismicJob, SeismicAxis, SeismicTrap, PortfolioSummary, IntelReport, TargetResult, DrillTarget } from './types';
import { ACTIVE_CAMPAIGN, INTEL_REPORTS, TASKING_REQUESTS, DATA_LAKE_FILES, TEMPORAL_DATA } from './constants';

const STORAGE_KEYS = {
  OVERRIDE: 'aurora_backend_url',
  ACTIVE_CAMPAIGN: 'aurora_active_id'
};

export class AuroraAPI {
  private static getBaseUrl(): string {
    return localStorage.getItem(STORAGE_KEYS.OVERRIDE) || 'https://aurora-osi-v4.up.railway.app';
  }

  static async init(): Promise<void> {
    console.log("Aurora Kernel Initialized at", this.getBaseUrl());
  }

  static async checkConnectivity(): Promise<ConnectivityResult> {
    try {
      const res = await fetch(`${this.getBaseUrl()}/system/health`, { method: 'GET' });
      if (res.ok) return { status: SystemStatus.ONLINE, mode: 'Cloud' };
    } catch (e) {
      console.warn("Uplink unstable, switching to Sovereign mode.");
    }
    return { status: SystemStatus.OFFLINE, mode: 'Sovereign', message: 'LOCAL_PHYSICS_ONLY' };
  }

  static isNeonActive(): boolean { return true; }
  static isGeePersistent(): boolean { return true; }
  static getActiveEndpoint(): string { return this.getBaseUrl(); }

  static setBackendUrl(url: string) {
    if (!url) localStorage.removeItem(STORAGE_KEYS.OVERRIDE);
    else localStorage.setItem(STORAGE_KEYS.OVERRIDE, url.trim());
  }

  private static async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.getBaseUrl()}${endpoint}`;
    try {
      const res = await fetch(url, {
        ...options,
        headers: { 'Content-Type': 'application/json', ...options.headers }
      });
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  static async getActiveCampaign(): Promise<ExplorationCampaign> {
    return (await this.request('/campaigns/active')) || ACTIVE_CAMPAIGN;
  }

  static async updateCampaign(campaign: ExplorationCampaign): Promise<void> {
    await this.request('/campaigns/update', {
      method: 'POST',
      body: JSON.stringify(campaign)
    });
  }

  static async getAllCampaigns(): Promise<ExplorationCampaign[]> {
    return (await this.request('/campaigns/all')) || [ACTIVE_CAMPAIGN];
  }

  static async getGlobalDiscoveries(): Promise<DiscoveryRecord[]> {
    return (await this.request('/discoveries/global')) || [];
  }

  static async launchRealMission(payload: any) {
    return await this.request('/mission/launch', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static async getMissionStatus(id: string) {
    return await this.request(`/mission/${id}/status`);
  }

  static async getReports() { return INTEL_REPORTS; }
  static async getTasks() { return TASKING_REQUESTS; }
  static async getDataLakeFiles() { return DATA_LAKE_FILES; }
  
  static async getSatelliteSchedule(lat: number, lon: number) {
    return (await this.request(`/gee/schedule?lat=${lat}&lon=${lon}`)) || { schedule: [] };
  }

  static async importCampaign(file: File): Promise<boolean> {
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      await this.updateCampaign(json);
      return true;
    } catch (e) { return false; }
  }

  static async submitTask(t: TaskingRequest) { return { status: 'success' }; }
  static async runPhysicsInversion(lat: number, lon: number, depth: number) { return { residuals: { mass_conservation: 0.0012, momentum_balance: 0.004 }, structure: "Anticline (Inferred)" }; }
  static async getPhysicsTomography(lat: number, lon: number) { return { slice: null }; }
  static generateLatentPoints(type: string, lat: number, lon: number, radiusKm: number = 10) { return []; }
  static async runQuantumOptimization(region: string, qubits: number, algo: string) { return { trace: [] }; }
  static async generateAndSaveReport(campaign: ExplorationCampaign): Promise<IntelReport> { return INTEL_REPORTS[0]; }
  static async getDataLakeStats() { return { hot_storage_pb: 4.2, cold_storage_pb: 12.1, daily_ingest_tb: 1.4 }; }
  static generateFileContent(n: string, t: any) { return "mock content"; }
  static async processFile(id: string, op: string) { return { id: `proc-${id}`, name: `Processed_${id}`, bucket: 'Processed', size: '1MB', type: 'NetCDF', lastModified: new Date().toISOString(), owner: 'System' } as DataObject; }
  static async getTemporalAnalysis(lat: number, lon: number) { return { data: TEMPORAL_DATA, trend: 'Stable', velocity_mm_yr: 0.2 }; }
  static async getDigitalTwinVoxels(lat: number, lon: number) { return { voxels: [] }; }
  static async getPortfolioOverview() { return { summary: { total_npv_usd: 1250000000, asset_count: 5, total_diesel_saved_l: 45000, total_water_saved_m3: 1200 }, assets: [] } as PortfolioSummary; }
  static async getSeismicSlice(lat: number, lon: number, index: number, axis: SeismicAxis) { return { width: 10, height: 10, data: [], uncertainty: [], horizons: [], faults: [], axis, index } as any; }
  static async getStructuralTraps(lat: number, lon: number) { return [] as SeismicTrap[]; }
  static async startSeismicJob(id: string) { return { id: `JOB-${id}`, status: 'Completed', progress: 100, currentTask: 'Done', logs: [], artifacts: {} } as SeismicJob; }
  static async fetchRealSpectralData(aoi: any, target: string) { return { spectrum: [] }; }
}