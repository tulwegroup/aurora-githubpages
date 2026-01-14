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

  private static getBaseUrl(): string {
      const override = localStorage.getItem(STORAGE_KEYS.BACKEND_OVERRIDE);
      // Fallback hierarchy: Override > Config > Hardcoded Fallback
      const rawUrl = override || APP_CONFIG.API.BASE_URL || 'https://aurora-backend-production.up.railway.app';
      return rawUrl.replace(/\/+$/, '');
  }

  /**
   * Initializes connection with the Railway/Neon stack.
   */
  static async init(): Promise<boolean> {
    this.baseUrl = this.getBaseUrl();
    try {
      const health = await this.checkConnectivity();
      this.isBackendOnline = health.status !== SystemStatus.OFFLINE;
      return this.isBackendOnline;
    } catch (e) {
      this.isBackendOnline = false;
      return false;
    }
  }

  static getActiveEndpoint = () => this.getBaseUrl();
  
  static setBackendUrl(url: string) {
      if (!url || url.trim() === '') {
          localStorage.removeItem(STORAGE_KEYS.BACKEND_OVERRIDE);
      } else {
          localStorage.setItem(STORAGE_KEYS.BACKEND_OVERRIDE, url.trim());
      }
      this.baseUrl = this.getBaseUrl();
  }
  
  static async checkConnectivity(): Promise<ConnectivityResult> {
    const url = this.getBaseUrl();
    const endpoints = ['/system/status', '/system/health', '/'];
    
    for (const endpoint of endpoints) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout
            
            const res = await fetch(`${url}${endpoint}`, { 
                signal: controller.signal,
                headers: { 'Accept': 'application/json' }
            });
            clearTimeout(timeoutId);
            
            if (res.ok) {
                try {
                    const data = await res.json();
                    this.serverStatus = data;
                } catch (e) {
                    this.serverStatus = { status: 'OK' }; 
                }
                
                return { 
                    status: SystemStatus.ONLINE, 
                    mode: 'Cloud',
                    message: 'LIVE_UPLINK_STABLE'
                };
            }
        } catch (e) {
            continue;
        }
    }
    
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

    const res = await fetch(fullUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  }

  static async launchRealMission(payload: any): Promise<any> {
    return this.apiFetch('/mission/launch', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  static async getMissionStatus(missionId: string): Promise<any> {
    return this.apiFetch(`/mission/${missionId}/status`);
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
        const res = await fetch(`${url}/campaigns/active`);
        if (res.ok) return await res.json();
    } catch(e) {}
    return ACTIVE_CAMPAIGN;
  }

  static async updateCampaign(campaign: ExplorationCampaign): Promise<void> {
    const url = this.getBaseUrl();
    try {
        await fetch(`${url}/campaigns/update`, { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(campaign) 
        });
    } catch(e) {}
  }

  static async getAllCampaigns(): Promise<ExplorationCampaign[]> {
    const url = this.getBaseUrl();
    try {
        const res = await fetch(`${url}/campaigns/all`);
        if (res.ok) return await res.json();
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

  static async fetchRealSpectralData(aoi: { lat: number, lon: number, radius_km: number }, target: string): Promise<any> {
    return this.apiFetch(`/gee/spectral?lat=${aoi.lat}&lon=${aoi.lon}&radius=${aoi.radius_km}&target=${target}`);
  }

  static async generateAndSaveReport(campaign: ExplorationCampaign): Promise<IntelReport> {
    return this.apiFetch(`/mission/${campaign.jobId}/report`);
  }
}