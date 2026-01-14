
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ExplorationCampaign, AppView, CAMPAIGN_PHASES, Anomaly, Satellite, TargetResult, ScanSector, MineralAgentType, HiveMindState } from '../types';
import { RESOURCE_CATALOG, ANOMALIES } from '../constants';
import MapVisualization from './MapVisualization';
import { Play, Upload, Plus, Target, Activity, Zap, Search, ChevronRight, AlertTriangle, CheckCircle, MapPin, Database, Radar, Globe, Crosshair, Loader2, FileText, Terminal, Bot, LayoutGrid, Users, Maximize, StopCircle, Cpu, Pause, Wifi, Lock, ShieldCheck, Server } from 'lucide-react';
import { AuroraAPI } from '../api';

interface DashboardProps {
    campaign: ExplorationCampaign;
    onLaunchCampaign: (campaign: ExplorationCampaign) => void;
    onAdvancePhase: () => void;
    onUpdateCampaign: (campaign: ExplorationCampaign) => void;
    onNavigate: (view: AppView) => void;
    hiveMindState: HiveMindState;
    setHiveMindState: React.Dispatch<React.SetStateAction<HiveMindState>>;
}

const Dashboard: React.FC<DashboardProps> = ({ campaign, onLaunchCampaign, onAdvancePhase, onUpdateCampaign, onNavigate, hiveMindState, setHiveMindState }) => {
    const [showMissionPlanner, setShowMissionPlanner] = useState(false);
    const [scanMode, setScanMode] = useState<'Regional' | 'Pinpoint' | 'HiveMind'>('Regional');
    const [missionConfig, setMissionConfig] = useState({
        coordinates: campaign.targetCoordinates || '',
        selectedResources: [] as string[],
        radius: campaign.radius || 50,
        name: ''
    });
    const [isLaunching, setIsLaunching] = useState(false);
    const [telemetryLogs, setTelemetryLogs] = useState<string[]>([]);
    const logsEndRef = useRef<HTMLDivElement>(null);
    const [systemOnline, setSystemOnline] = useState(false);

    const addLog = useCallback((msg: string) => {
        const time = new Date().toLocaleTimeString();
        setTelemetryLogs(prev => [...prev, `[${time}] ${msg}`]);
    }, []);

    // Initial Setup
    useEffect(() => {
        const checkHealth = async () => {
            const health = await AuroraAPI.checkConnectivity();
            setSystemOnline(health.status === 'ONLINE');
        };
        checkHealth();
    }, []);

    // Polling for mission status if a jobId exists
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
                        addLog("MISSION COMPLETE: Spectral analysis confirmed.");
                        clearInterval(interval);
                    }
                } catch (e) {
                    console.error("Polling failed", e);
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
        addLog("Initializing GEE Data Acquisition...");
        
        try {
            const missionId = `mission-${Date.now()}`;
            const payload = {
                mission_id: missionId,
                aoi: { lat: 38.5, lon: -117.5, radius_km: missionConfig.radius }, 
                minerals: missionConfig.selectedResources.map(r => r.toLowerCase()),
                priority: "high"
            };

            await AuroraAPI.launchRealMission(payload);
            addLog("Backend handshake success. Launching Worker...");
            
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
            addLog("Mission parameters locked. Processing multi-physics stack...");
        } catch (error) {
            addLog("NOTICE: Running in Autonomous Sovereign Mode.");
            const newCampaign: ExplorationCampaign = {
                ...campaign,
                id: `CMP-${Date.now()}`,
                name: missionConfig.name || `Scan: ${missionConfig.coordinates}`,
                targetCoordinates: missionConfig.coordinates,
                radius: missionConfig.radius,
                status: 'Active',
                phaseProgress: 0,
                autoPlay: true 
            };
            onLaunchCampaign(newCampaign);
            setShowMissionPlanner(false);
        } finally {
            setIsLaunching(false);
        }
    };

    const groupedMinerals = RESOURCE_CATALOG.reduce((acc, curr: any) => {
        const group = curr.group || 'Other';
        if (!acc[group]) acc[group] = [];
        acc[group].push(curr);
        return acc;
    }, {} as Record<string, any[]>);

    return (
        <div className="space-y-6 pb-20">
            {/* Summary Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                        <Activity size={80} />
                    </div>
                    <p className="text-xs text-slate-400 font-mono uppercase mb-1">Mission State</p>
                    <h3 className="text-xl font-bold text-white flex items-center">
                        {campaign.status.toUpperCase()}
                        {campaign.status === 'Active' && <span className="ml-2 w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>}
                    </h3>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-4">
                        <div className="bg-emerald-500 h-full transition-all" style={{ width: `${campaign.phaseProgress}%` }}></div>
                    </div>
                </div>

                <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6">
                    <p className="text-xs text-slate-400 font-mono uppercase mb-1">Active Target</p>
                    <h3 className="text-lg font-bold text-white truncate">{campaign.regionName || campaign.targetCoordinates}</h3>
                    <p className="text-[10px] text-slate-500 mt-1 font-mono uppercase tracking-widest">{campaign.id}</p>
                </div>

                <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6 flex flex-col justify-between">
                    <div>
                        <p className="text-xs text-slate-400 font-mono uppercase mb-1">Stack Status</p>
                        <h3 className={`text-lg font-bold flex items-center ${systemOnline ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {systemOnline ? <ShieldCheck size={18} className="mr-2"/> : <Lock size={18} className="mr-2"/>}
                            {systemOnline ? 'CLOUD_GOVERNED' : 'SOVEREIGN_NODE'}
                        </h3>
                    </div>
                    <div className="text-[9px] text-slate-500 font-mono border-t border-slate-800 pt-2 flex justify-between">
                        <span>GEE: {AuroraAPI.isGeePersistent() ? 'ACTIVE' : 'READY'}</span>
                        <span>DB: {AuroraAPI.isNeonActive() ? 'LIVE' : 'LOCAL'}</span>
                    </div>
                </div>

                <button 
                    onClick={() => setShowMissionPlanner(true)}
                    className="bg-aurora-600 hover:bg-aurora-500 border border-aurora-400/30 rounded-xl p-6 flex flex-col justify-center items-center text-center transition-all shadow-lg hover:shadow-aurora-500/20 group"
                >
                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                        <Plus size={20} className="text-white" />
                    </div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Configure Mission</h3>
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-aurora-950 border border-aurora-800 rounded-xl h-[500px] relative overflow-hidden shadow-2xl group">
                        <div className="absolute top-4 left-4 z-10 bg-black/60 backdrop-blur px-3 py-1 rounded text-xs font-mono text-emerald-400 border border-emerald-500/30 flex items-center">
                            <Radar size={14} className="mr-2 animate-spin-slow" />
                            {systemOnline ? 'LIVE SATELLITE TELEMETRY' : 'SOVEREIGN PHYSICS LAYER'}
                        </div>
                        <MapVisualization 
                            anomalies={ANOMALIES}
                            onSelectAnomaly={() => {}}
                            selectedAnomaly={null}
                            centerCoordinates={campaign.targetCoordinates}
                            className="w-full h-full"
                        />
                    </div>

                    {showMissionPlanner && (
                        <div className="bg-aurora-900 border border-aurora-500 rounded-xl p-6 animate-fadeIn shadow-2xl z-20 relative">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-xl font-bold text-white flex items-center">
                                    <Zap className="mr-3 text-aurora-500" /> Mission Architecture
                                </h3>
                                <button onClick={() => setShowMissionPlanner(false)} className="text-slate-500 hover:text-white"><StopCircle size={20}/></button>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest">Geospatial Focus</label>
                                    <input 
                                        type="text" 
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-aurora-500 font-mono text-sm"
                                        placeholder="Lat, Lon"
                                        value={missionConfig.coordinates}
                                        onChange={e => setMissionConfig({...missionConfig, coordinates: e.target.value})}
                                    />
                                    
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-4">Scan Radius (km)</label>
                                    <input 
                                        type="range" min="1" max="150" 
                                        className="w-full accent-aurora-500"
                                        value={missionConfig.radius}
                                        onChange={e => setMissionConfig({...missionConfig, radius: parseInt(e.target.value)})}
                                    />
                                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                                        <span>1km</span>
                                        <span>{missionConfig.radius}km</span>
                                        <span>150km</span>
                                    </div>
                                </div>

                                <div className="space-y-4 flex flex-col">
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest">Target Mineral Library</label>
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
                                disabled={isLaunching}
                                className="w-full mt-8 bg-aurora-600 hover:bg-aurora-500 text-white font-bold py-4 rounded-xl flex items-center justify-center transition-all shadow-xl active:scale-95"
                            >
                                {isLaunching ? <Loader2 className="animate-spin mr-3"/> : <Target className="mr-3"/>} 
                                {isLaunching ? 'COMMENCING ANALYTICS...' : 'LAUNCH MISSION'}
                            </button>
                        </div>
                    )}
                </div>

                <div className="space-y-6">
                    <div className="bg-aurora-950 border border-aurora-800 rounded-xl p-6 h-[500px] flex flex-col shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/50"></div>
                        <h3 className="font-bold text-slate-400 mb-4 flex items-center justify-between">
                            <span className="flex items-center"><Terminal size={14} className="mr-2 text-emerald-500" /> KERNEL TELEMETRY</span>
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        </h3>
                        <div className="flex-1 overflow-y-auto custom-scrollbar font-mono text-[10px] space-y-2 pr-2">
                            {telemetryLogs.length === 0 ? (
                                <div className="text-slate-700 italic">Waiting for telemetry lock...</div>
                            ) : (
                                telemetryLogs.map((log, i) => (
                                    <div key={i} className="text-emerald-400/80 border-b border-white/5 pb-1 last:border-0">{log}</div>
                                ))
                            )}
                            <div ref={logsEndRef} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
