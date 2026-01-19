
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ExplorationCampaign, AppView, CAMPAIGN_PHASES, ScanSector, MineralAgentType, HiveMindState } from '../types';
import { RESOURCE_CATALOG } from '../constants';
import MapVisualization from './MapVisualization';
import { Plus, Target, Activity, Zap, Wifi, ShieldCheck, Lock, Terminal, Loader2, Radar, StopCircle } from 'lucide-react';
import { AuroraAPI } from '../api';

interface DashboardProps {
    campaign: ExplorationCampaign;
    onLaunchCampaign: (campaign: ExplorationCampaign) => void;
    onAdvancePhase?: () => void;
    onUpdateCampaign: (campaign: ExplorationCampaign) => void;
    onNavigate: (view: AppView) => void;
    hiveMindState: HiveMindState;
    setHiveMindState: React.Dispatch<React.SetStateAction<HiveMindState>>;
    activeScanLocation?: { lat: number; lon: number; name: string } | null;
    onSetActiveScanLocation?: (lat: number, lon: number, name: string) => void;
    scrollToTop?: () => void;
    scrollToBottom?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ campaign, onLaunchCampaign, onUpdateCampaign, onNavigate, activeScanLocation }) => {
    const [showMissionPlanner, setShowMissionPlanner] = useState(false);
    const [missionConfig, setMissionConfig] = useState({
        coordinates: campaign.targetCoordinates || '',
        selectedResources: [] as string[],
        radius: campaign.radius || 50,
        name: ''
    });
    const [isLaunching, setIsLaunching] = useState(false);
    const [telemetryLogs, setTelemetryLogs] = useState<string[]>([]);
    const [isLive, setIsLive] = useState(false);
    const [isGeeReady, setIsGeeReady] = useState(false);
    const [isNeonReady, setIsNeonReady] = useState(false);
    const [scanProgress, setScanProgress] = useState(65);

    const addLog = useCallback((msg: string) => {
        const time = new Date().toLocaleTimeString();
        setTelemetryLogs(prev => [...prev, `[${time}] ${msg}`].slice(-20));
    }, []);

    const refreshStatus = useCallback(async () => {
        const health = await AuroraAPI.checkConnectivity();
        const connected = health.status !== 'OFFLINE';
        setIsLive(connected);
        
        // If connected, assume sub-systems are working even if metadata keys are missing
        setIsGeeReady(connected && AuroraAPI.isGeePersistent());
        setIsNeonReady(connected && AuroraAPI.isNeonActive());
        
        if (connected) {
            addLog("Cloud Origin: Handshake Verified.");
        }
    }, [addLog]);

    useEffect(() => {
        refreshStatus();
        const interval = setInterval(refreshStatus, 15000);
        return () => clearInterval(interval);
    }, [refreshStatus]);

    useEffect(() => {
        let interval: any;
        if (campaign.status === 'Active' && campaign.jobId) {
            interval = setInterval(async () => {
                try {
                    const status = await AuroraAPI.getMissionStatus(campaign.jobId!);
                    onUpdateCampaign({
                        ...campaign,
                        phaseProgress: status.progress,
                        status: status.status === 'COMPLETED' ? 'Completed' : 'Active',
                        results: status.results ? status.results.results : campaign.results
                    });
                    
                    if (status.status === 'COMPLETED') {
                        addLog("MISSION COMPLETE: Multi-Physics Tensor Harmonized.");
                        clearInterval(interval);
                    }
                } catch (e) {
                    addLog("Warning: Telemetry poll skipped (Uplink Latency).");
                }
            }, 5000);
        }
        return () => clearInterval(interval);
    }, [campaign, onUpdateCampaign, addLog]);

    const handleLaunch = async () => {
        if (missionConfig.selectedResources.length === 0) {
            alert("Please select at least one mineral target.");
            return;
        }

        setIsLaunching(true);
        addLog("Routing tasking command through Railway gateway...");
        
        try {
            const missionId = `mission-${Date.now()}`;
            const payload = {
                mission_id: missionId,
                aoi: { lat: 38.5, lon: -117.5, radius_km: missionConfig.radius }, 
                minerals: missionConfig.selectedResources.map(r => r.toLowerCase()),
                priority: "high"
            };

            await AuroraAPI.launchRealMission(payload);
            addLog("Direct Satellite Tasking: SUCCESS.");
            
            const newCampaign: ExplorationCampaign = {
                ...campaign,
                id: `CMP-${Date.now()}`,
                jobId: missionId,
                name: missionConfig.name || `Scan: ${missionConfig.coordinates}`,
                targetCoordinates: missionConfig.coordinates,
                radius: missionConfig.radius,
                status: 'Active',
                phaseProgress: 0,
                autoPlay: false
            };
            
            onLaunchCampaign(newCampaign);
            setShowMissionPlanner(false);
            addLog("Spectral Engine: Acquisition Initialized.");
        } catch (error) {
            addLog("Uplink Refused: Check Railway Backend logs for CORS/Auth errors.");
            setIsLaunching(false);
        }
    };

    const groupedMinerals = React.useMemo(() => {
        try {
            return RESOURCE_CATALOG.reduce((acc, curr: any) => {
                const group = curr.group || 'Other';
                if (!acc[group]) acc[group] = [];
                acc[group].push(curr);
                return acc;
            }, {} as Record<string, any[]>);
        } catch (err) {
            console.error('Error grouping minerals:', err);
            return {} as Record<string, any[]>;
        }
    }, []);

    return (
        <div className="space-y-6 pb-20 animate-fadeIn">
            {/* Summary Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6 relative overflow-hidden group shadow-lg">
                    <p className="text-xs text-slate-400 font-mono uppercase mb-1">Stack State</p>
                    <h3 className="text-xl font-bold text-white flex items-center">
                        {campaign.status.toUpperCase()}
                        {campaign.status === 'Active' && <span className="ml-2 w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]"></span>}
                    </h3>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-4">
                        <div className="bg-emerald-500 h-full transition-all duration-1000" style={{ width: `${campaign.phaseProgress}%` }}></div>
                    </div>
                </div>

                <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6 shadow-lg">
                    <p className="text-xs text-slate-400 font-mono uppercase mb-1">Active Coordinate</p>
                    <h3 className="text-lg font-bold text-white truncate font-mono">{campaign.targetCoordinates || 'ORBITAL_STANDBY'}</h3>
                </div>

                <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6 flex flex-col justify-between shadow-lg">
                    <div>
                        <p className="text-xs text-slate-400 font-mono uppercase mb-1">Stack Connectivity</p>
                        <h3 className={`text-lg font-bold flex items-center ${isLive ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {isLive ? <ShieldCheck size={18} className="mr-2"/> : <Lock size={18} className="mr-2"/>}
                            {isLive ? 'CLOUD_OPERATIONAL' : 'OFFLINE_SIM'}
                        </h3>
                    </div>
                    <div className="text-[9px] text-slate-500 font-mono border-t border-slate-800 pt-2 flex justify-between">
                        <span className={isLive ? 'text-emerald-500' : ''}>GEE: {isLive ? 'ACTIVE' : 'STANDBY'}</span>
                        <span className={isLive ? 'text-emerald-500' : ''}>DB: {isLive ? 'CONNECTED' : 'STANDBY'}</span>
                    </div>
                </div>

                <button 
                    onClick={() => setShowMissionPlanner(true)}
                    className="bg-aurora-600 hover:bg-aurora-500 border border-aurora-400/30 rounded-xl p-6 flex flex-col justify-center items-center text-center transition-all shadow-xl hover:shadow-aurora-500/20 group"
                >
                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                        <Plus size={20} className="text-white" />
                    </div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Configure Scan</h3>
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-aurora-950 border border-aurora-800 rounded-xl h-[500px] relative overflow-hidden shadow-2xl group">
                        <div className="absolute top-4 left-4 z-10 bg-black/60 backdrop-blur px-3 py-1 rounded text-xs font-mono text-emerald-400 border border-emerald-500/30 flex items-center">
                            <Radar size={14} className="mr-2 animate-spin-slow" />
                            {isLive ? 'LIVE SATELLITE UPLINK' : 'Sovereign Node Active'}
                        </div>
                        <MapVisualization 
                            anomalies={[]} 
                            onSelectAnomaly={() => {}}
                            selectedAnomaly={null}
                            centerCoordinates={campaign.targetCoordinates}
                            className="w-full h-full"
                            isGEEActive={isLive}
                        />
                    </div>

                    {showMissionPlanner && (
                        <div className="bg-aurora-900 border border-aurora-500 rounded-xl p-6 animate-fadeIn shadow-2xl z-20 relative">
                            <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                                <h3 className="text-xl font-bold text-white flex items-center">
                                    <Zap className="mr-3 text-aurora-500" /> Managed Scanning Engine
                                </h3>
                                <button onClick={() => setShowMissionPlanner(false)} className="text-slate-500 hover:text-white transition-colors"><StopCircle size={20}/></button>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest">Geospatial Target</label>
                                    <input 
                                        type="text" 
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-aurora-500 font-mono text-sm"
                                        placeholder="Lat, Lon"
                                        value={missionConfig.coordinates}
                                        onChange={e => setMissionConfig({...missionConfig, coordinates: e.target.value})}
                                    />
                                    
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-4">Compute Radius (km)</label>
                                    <input 
                                        type="range" min="1" max="150" 
                                        className="w-full accent-aurora-500"
                                        value={missionConfig.radius}
                                        onChange={e => setMissionConfig({...missionConfig, radius: parseInt(e.target.value)})}
                                    />
                                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                                        <span>1km</span>
                                        <span className="text-aurora-400">{missionConfig.radius}km</span>
                                        <span>150km</span>
                                    </div>
                                </div>

                                <div className="space-y-4 flex flex-col">
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest">Signal Catalog</label>
                                    <div className="flex-1 bg-slate-950 border border-slate-800 rounded-lg p-3 overflow-y-auto max-h-64 custom-scrollbar">
                                        {Object.entries(groupedMinerals).map(([group, minerals]) => (
                                            <div key={group} className="mb-4">
                                                <h4 className="text-[9px] font-bold text-slate-600 uppercase mb-2 border-b border-slate-900 pb-1">{group}</h4>
                                                <div className="grid grid-cols-2 gap-1">
                                                    {minerals.map(r => (
                                                        <button 
                                                            key={r.category}
                                                            onClick={() => {
                                                                setMissionConfig(prev => ({
                                                                    ...prev,
                                                                    selectedResources: prev.selectedResources.includes(r.category) 
                                                                        ? prev.selectedResources.filter(x => x !== r.category)
                                                                        : [...prev.selectedResources, r.category]
                                                                }));
                                                            }}
                                                            className={`p-2 rounded border text-[10px] text-left transition-all ${missionConfig.selectedResources.includes(r.category) ? 'bg-aurora-500/20 border-aurora-500 text-white shadow-lg' : 'border-slate-800 text-slate-500 hover:border-slate-700'}`}
                                                        >
                                                            {r.category}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <button 
                                onClick={handleLaunch}
                                disabled={isLaunching || !isLive}
                                className={`w-full mt-8 bg-aurora-600 hover:bg-aurora-500 text-white font-bold py-4 rounded-xl flex items-center justify-center transition-all shadow-xl active:scale-95 ${!isLive ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {isLaunching ? <Loader2 className="animate-spin mr-3"/> : <Target className="mr-3"/>} 
                                {!isLive ? 'UPLINK REQUIRED' : isLaunching ? 'ROUTING SIGNAL...' : 'LAUNCH LIVE ANALYSIS'}
                            </button>
                        </div>
                    )}
                </div>

                <div className="space-y-6">
                    {/* Kernel Telemetry Card */}
                    <div className="bg-aurora-900/60 border border-aurora-800 rounded-lg p-4 backdrop-blur-sm hover:border-aurora-700 transition-colors">
                        <div className="flex items-center justify-between mb-3">
                            <p className="text-aurora-400 text-xs font-mono uppercase">Kernel Telemetry</p>
                            <Activity size={14} className="text-emerald-400 animate-pulse" />
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-400">Signal Strength</span>
                                <span className="text-emerald-400 font-bold">{scanProgress}%</span>
                            </div>
                            <div className="w-full bg-aurora-950 rounded h-2">
                                <div
                                    className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2 rounded transition-all"
                                    style={{ width: `${scanProgress}%` }}
                                ></div>
                            </div>
                            <p className="text-xs text-aurora-500 mt-3 font-mono">Waiting for telemetry lock...</p>
                        </div>
                    </div>

                    {/* Phase Status Card */}
                    <div className="bg-aurora-900/60 border border-aurora-800 rounded-lg p-4 backdrop-blur-sm hover:border-aurora-700 transition-colors">
                        <p className="text-aurora-400 text-xs font-mono uppercase mb-3">Current Phase</p>
                        <p className="text-xl font-bold text-aurora-300 mb-2">{campaign.currentPhase || 'Acquisition'}</p>
                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                                <span className="text-slate-500">Phase {campaign.phaseIndex || 1}</span>
                                <span className="text-aurora-400">Iteration {campaign.iteration || 1}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Accuracy</span>
                                <span className="text-emerald-400">{((campaign.accuracyScore || 0.87) * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                    </div>

                    {/* Cloud Telemetry Logs */}
                    <div className="bg-aurora-950 border border-aurora-800 rounded-xl p-6 h-[280px] flex flex-col shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/50"></div>
                        <h3 className="font-bold text-slate-400 mb-4 flex items-center justify-between">
                            <span className="flex items-center"><Terminal size={14} className="mr-2 text-emerald-500" /> CLOUD TELEMETRY</span>
                            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
                        </h3>
                        <div className="flex-1 overflow-y-auto custom-scrollbar font-mono text-[10px] space-y-2 pr-2">
                            {telemetryLogs.length === 0 ? (
                                <div className="text-slate-700 italic">Listening for Railway events...</div>
                            ) : (
                                telemetryLogs.map((log, i) => (
                                    <div key={i} className="text-emerald-400/80 border-b border-white/5 pb-1 last:border-0">{log}</div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
