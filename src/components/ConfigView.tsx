import React, { useState, useEffect, useCallback } from 'react';
import { 
    Server, Database, ShieldCheck, 
    RefreshCw, Lock, Link, Save, Terminal, Activity, Zap, Info, Globe, Cpu
} from 'lucide-react';
import { AuroraAPI } from '../api';

const ConfigView: React.FC = () => {
    const [isChecking, setIsChecking] = useState(false);
    const [manualUrl, setManualUrl] = useState(AuroraAPI.getActiveEndpoint());
    const [status, setStatus] = useState({
        backend: 'UNKNOWN',
        database: 'UNKNOWN',
        gee: 'UNKNOWN',
        latency: '0ms'
    });
    const [logs, setLogs] = useState<string[]>([]);

    const addLog = useCallback((msg: string) => {
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 12));
    }, []);

    const runDiagnostics = useCallback(async () => {
        if (isChecking) return;
        setIsChecking(true);
        const startTime = Date.now();
        const currentEndpoint = AuroraAPI.getActiveEndpoint();
        
        try {
            const health = await AuroraAPI.checkConnectivity();
            const duration = Date.now() - startTime;
            const connected = health.status !== 'OFFLINE';
            
            const dbActive = connected && AuroraAPI.isNeonActive();
            const geeActive = connected && AuroraAPI.isGeePersistent();

            setStatus({
                backend: connected ? 'OPERATIONAL' : 'UNREACHABLE',
                database: connected ? (dbActive ? 'SYNCHRONIZED' : 'STANDBY') : 'OFFLINE',
                gee: connected ? (geeActive ? 'KERNEL_ACTIVE' : 'INITIALIZING') : 'OFFLINE',
                latency: `${duration}ms`
            });
            
            if (connected) {
                addLog(`Handshake: Cloud Stack reachable at ${currentEndpoint}`);
                addLog(`Latency: ${duration}ms RTT measured.`);
            } else {
                addLog(`Error: Connection refused for ${currentEndpoint}`);
            }
        } catch (e: any) {
            addLog(`Critical: Handshake failure - ${e.message}`);
            setStatus(prev => ({ ...prev, backend: 'UNREACHABLE' }));
        } finally {
            setIsChecking(false);
        }
    }, [addLog, isChecking]);

    // Stable effect with correct dependency handling to stop flickering
    useEffect(() => {
        runDiagnostics();
        const interval = setInterval(runDiagnostics, 60000); // Check once per minute
        return () => clearInterval(interval);
    }, [runDiagnostics]);

    const handleUrlUpdate = async () => {
        AuroraAPI.setBackendUrl(manualUrl);
        addLog(`System: Uplink redirected to ${manualUrl}`);
        // Force immediate check
        setIsChecking(false);
        setTimeout(runDiagnostics, 100);
    };

    return (
        <div className="space-y-6 max-w-6xl mx-auto pb-20 animate-fadeIn">
            {/* Header: Infrastructure Governance */}
            <div className="bg-aurora-900/40 border border-aurora-800 rounded-2xl p-8 relative overflow-hidden shadow-2xl">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                    <ShieldCheck size={160} />
                </div>
                <div className="flex justify-between items-start relative z-10">
                    <div>
                        <h2 className="text-3xl font-bold text-white flex items-center tracking-tight font-mono uppercase">
                            <Lock className="mr-4 text-aurora-400" size={32} /> System_Governance
                        </h2>
                        <p className="text-slate-400 mt-2 max-w-2xl leading-relaxed">
                            Aurora OSI v3 manages infrastructure parameters via encrypted server-side secrets. 
                            If the system is <strong>UNREACHABLE</strong>, use the override below to specify your 
                            Railway public URL.
                        </p>
                    </div>
                    <button 
                        onClick={runDiagnostics} 
                        disabled={isChecking}
                        className="flex items-center space-x-2 px-4 py-2 bg-slate-900 border border-aurora-800 hover:border-aurora-500 text-white rounded-xl transition-all shadow-lg active:scale-95 disabled:opacity-50"
                    >
                        <RefreshCw size={18} className={isChecking ? 'animate-spin' : ''} />
                        <span className="text-xs font-bold font-mono">FORCE_PROBE</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    
                    {/* Manual Uplink Override - HIGHLIGHTED */}
                    <div className="bg-slate-900 border-2 border-aurora-500/40 p-6 rounded-2xl shadow-[0_0_30px_rgba(34,211,238,0.1)] backdrop-blur-md">
                        <div className="flex items-center mb-4">
                            <div className="p-2 bg-aurora-500/20 rounded-lg mr-3">
                                <Link size={20} className="text-aurora-400" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white text-sm uppercase tracking-widest">Manual Uplink Override</h3>
                                <p className="text-[10px] text-slate-500 font-mono">ACTIVE_ORIGIN: {AuroraAPI.getActiveEndpoint()}</p>
                            </div>
                        </div>
                        
                        <div className="flex flex-col sm:flex-row gap-3">
                            <input 
                                type="text"
                                value={manualUrl}
                                onChange={(e) => setManualUrl(e.target.value)}
                                className="flex-1 bg-black/50 border border-slate-700 rounded-xl px-4 py-3 text-sm font-mono text-emerald-400 focus:border-aurora-500 outline-none transition-all placeholder:text-slate-800"
                                placeholder="https://your-app.up.railway.app"
                            />
                            <button 
                                onClick={handleUrlUpdate}
                                className="bg-aurora-600 hover:bg-aurora-500 text-white px-8 py-3 rounded-xl text-sm font-bold flex items-center justify-center transition-all shadow-lg active:scale-95"
                            >
                                <Save size={18} className="mr-2" /> SYNCHRONIZE
                            </button>
                        </div>
                        <p className="mt-3 text-[10px] text-slate-600 flex items-center">
                            <Info size={12} className="mr-1" /> Updates are persistent and stored in secure browser enclave.
                        </p>
                    </div>

                    {/* Status Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between h-40 shadow-inner">
                            <div className="flex justify-between items-start">
                                <Server className={status.backend === 'OPERATIONAL' ? 'text-emerald-400' : 'text-red-400'} size={24} />
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${status.backend === 'OPERATIONAL' ? 'bg-emerald-950 text-emerald-400 border-emerald-500/30' : 'bg-red-950 text-red-400 border-red-500/30'}`}>
                                    {status.backend}
                                </span>
                            </div>
                            <div>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Compute Core</p>
                                <p className="text-xs font-mono text-slate-400 mt-1">Railway Managed Proxy</p>
                            </div>
                        </div>

                        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between h-40 shadow-inner">
                            <div className="flex justify-between items-start">
                                <Database className={status.database === 'SYNCHRONIZED' ? 'text-aurora-400' : 'text-slate-500'} size={24} />
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${status.database === 'SYNCHRONIZED' ? 'bg-aurora-950 text-aurora-400 border-aurora-500/30' : 'bg-slate-950 text-slate-500 border-slate-800'}`}>
                                    {status.database}
                                </span>
                            </div>
                            <div>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Persistence</p>
                                <p className="text-xs font-mono text-slate-400 mt-1">Neon Serverless Storage</p>
                            </div>
                        </div>

                        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between h-40 shadow-inner">
                            <div className="flex justify-between items-start">
                                <Zap className={status.gee === 'KERNEL_ACTIVE' ? 'text-amber-400' : 'text-slate-500'} size={24} />
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${status.gee === 'KERNEL_ACTIVE' ? 'bg-amber-950 text-amber-400 border-amber-500/30' : 'bg-slate-950 text-slate-500 border-slate-800'}`}>
                                    {status.gee}
                                </span>
                            </div>
                            <div>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Spectral Engine</p>
                                <p className="text-xs font-mono text-slate-400 mt-1">Google Earth Engine</p>
                            </div>
                        </div>

                        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between h-40 shadow-inner">
                            <div className="flex justify-between items-start">
                                <Activity className="text-emerald-400" size={24} />
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded border bg-slate-950 text-emerald-400 border-emerald-500/30 font-mono">
                                    {status.latency}
                                </span>
                            </div>
                            <div>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Handshake Health</p>
                                <p className="text-xs font-mono text-slate-400 mt-1">Managed VPC Tunnel</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-2xl flex flex-col overflow-hidden h-[400px] lg:h-auto shadow-2xl">
                    <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
                        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center font-mono">
                            <Terminal size={14} className="mr-2 text-emerald-400" /> Stack_Telemetry
                        </h3>
                        <div className={`w-2 h-2 rounded-full ${status.backend === 'OPERATIONAL' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                    </div>
                    <div className="flex-1 p-4 font-mono text-[10px] space-y-2 overflow-y-auto custom-scrollbar bg-black/40">
                        {logs.length === 0 ? (
                            <p className="text-slate-700 italic">Listening for system events...</p>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="text-slate-400 flex gap-2 border-l border-slate-800 pl-2 group">
                                    <span className="text-slate-600 shrink-0">{log.split('] ')[0]}]</span>
                                    <span className={log.includes('Handshake') || log.includes('Latency') ? 'text-emerald-500' : ''}>
                                        {log.split('] ')[1]}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ConfigView;