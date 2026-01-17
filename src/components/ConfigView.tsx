import React, { useState, useEffect, useCallback } from 'react';
import { 
    Server, Database, ShieldCheck, 
    RefreshCw, Lock, Link, Save, Terminal, Activity, Zap, Info, Globe, Cpu,
    MapPin, Radio, Layers, Search, BarChart3, Clock
} from 'lucide-react';
import { AuroraAPI } from '../api';
import { updateActiveCampaign, formatCoordinates } from '../constants';
import ScanStatusMonitor from './ScanStatusMonitor';

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
    const [activeScanId, setActiveScanId] = useState<string | null>(null);

    // Scan Configuration State
    const [scanConfig, setScanConfig] = useState({
        scanType: 'radius' as 'point' | 'radius' | 'grid',
        latitude: -10.5,
        longitude: -35.3,
        country: 'Tanzania',
        region: 'Tanzanian Craton',
        radiusKm: 50,
        gridSpacingM: 30,
        minerals: ['gold', 'lithium', 'copper'],
        resolution: 'native' as 'native' | 'high' | 'medium' | 'low',
        sensor: 'Sentinel-2',
        maxCloudCoverPercent: 20,
        dateStart: '',
        dateEnd: ''
    });

    const [scanHistory, setScanHistory] = useState<any[]>([]);
    const [isScanning, setIsScanning] = useState(false);
    const [selectedMinerals, setSelectedMinerals] = useState<Set<string>>(
        new Set(scanConfig.minerals)
    );

    const availableMinerals = [
        // Precious Metals (3)
        'gold', 'silver', 'platinum',
        // Base Metals (6)
        'copper', 'molybdenum', 'zinc', 'lead', 'nickel', 'cobalt',
        // Battery & Energy Metals (2)
        'lithium', 'rare_earth_elements',
        // Deep-Sea Minerals (3)
        'cobalt_crust', 'polymetallic_nodules', 'hydrothermal_sulfides',
        // Industrial Minerals (5)
        'potash', 'phosphate', 'sulfur', 'barite', 'fluorspar',
        // Bulk Commodities (3)
        'iron_ore', 'manganese', 'aluminum',
        // Hydrocarbons (3)
        'crude_oil', 'natural_gas', 'coal',
        // Geothermal & Renewable (2)
        'geothermal_hot_spring', 'geothermal_deep',
        // Water Resources (1)
        'groundwater_aquifer',
        // Aggregates (1)
        'aggregate'
    ];

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
            addLog(`Error during diagnostics: ${e.message}`);
            setStatus(prev => ({...prev, backend: 'ERROR'}));
        } finally {
            setIsChecking(false);
        }
    }, [addLog]);

    const loadScanHistory = useCallback(async () => {
        try {
            const response = await fetch('/scans?limit=10');
            if (response.ok) {
                const data = await response.json();
                setScanHistory(data.scans || []);
                addLog(`Loaded ${data.scans?.length || 0} previous scans`);
            }
        } catch (e) {
            addLog(`Failed to load scan history: ${e}`);
        }
    }, [addLog]);

    const handleMineralToggle = (mineral: string) => {
        const newSet = new Set(selectedMinerals);
        if (newSet.has(mineral)) {
            newSet.delete(mineral);
        } else {
            newSet.add(mineral);
        }
        setSelectedMinerals(newSet);
        setScanConfig(prev => ({
            ...prev,
            minerals: Array.from(newSet)
        }));
    };

    const handleStartScan = async () => {
        if (selectedMinerals.size === 0) {
            addLog('Error: Select at least one mineral to scan');
            return;
        }

        setIsScanning(true);
        addLog(`🔍 Initiating ${scanConfig.scanType} scan for ${Array.from(selectedMinerals).join(', ')}`);

        try {
            const requestBody = {
                scan_type: scanConfig.scanType,
                latitude: parseFloat(scanConfig.latitude as any),
                longitude: parseFloat(scanConfig.longitude as any),
                country: scanConfig.country || null,
                region: scanConfig.region || null,
                radius_km: scanConfig.scanType === 'radius' ? parseFloat(scanConfig.radiusKm as any) : 0,
                grid_spacing_m: scanConfig.scanType === 'grid' ? parseFloat(scanConfig.gridSpacingM as any) : 30,
                minerals: Array.from(selectedMinerals),
                resolution: scanConfig.resolution,
                sensor: scanConfig.sensor,
                max_cloud_cover_percent: parseFloat(scanConfig.maxCloudCoverPercent as any),
                date_start: scanConfig.dateStart || undefined,
                date_end: scanConfig.dateEnd || undefined
            };

            const response = await fetch('/scans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (response.ok) {
                const result = await response.json();
                const scanId = result.scan_id;
                
                // Update active campaign with new scan parameters
                updateActiveCampaign(
                    parseFloat(scanConfig.latitude as any),
                    parseFloat(scanConfig.longitude as any),
                    Array.from(selectedMinerals),
                    scanConfig.country || undefined,
                    scanConfig.region || undefined
                );
                
                // Set active scan for monitoring
                setActiveScanId(scanId);
                
                addLog(`✓ Scan ${scanId} queued - processing in background`);
                addLog(`📍 Target: ${formatCoordinates(parseFloat(scanConfig.latitude as any), parseFloat(scanConfig.longitude as any))}`);
                
                // Reload history
                await loadScanHistory();
            } else {
                const error = await response.json();
                addLog(`✗ Scan failed: ${error.detail || 'Unknown error'}`);
            }
        } catch (e: any) {
            addLog(`✗ Scan request error: ${e.message}`);
        } finally {
            setIsScanning(false);
        }
    };

    useEffect(() => {
        runDiagnostics();
        loadScanHistory();
        const interval = setInterval(runDiagnostics, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleUrlUpdate = async () => {
        AuroraAPI.setBackendUrl(manualUrl);
        addLog(`System: Uplink redirected to ${manualUrl}`);
        setIsChecking(false);
        setTimeout(() => runDiagnostics(), 100);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-8">
            {/* Header */}
            <div className="mb-12">
                <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
                    <Server className="text-cyan-400" size={40} />
                    Infrastructure & Mission Configuration
                </h1>
                <p className="text-slate-400">Dynamic target region based on scan coordinates</p>
            </div>

            {/* Active Scan Monitor */}
            {activeScanId && (
                <ScanStatusMonitor scanId={activeScanId} isVisible={!!activeScanId} />
            )}

            {/* Sync Diagnostics Card */}
            <div className="mb-8 bg-gradient-to-r from-slate-800 to-slate-700 rounded-lg p-8 border border-cyan-500/20">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold flex items-center gap-3">
                        <Radio className="text-green-400" size={28} />
                        Sync_Diagnostics
                    </h2>
                    <button
                        onClick={runDiagnostics}
                        disabled={isChecking}
                        className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 px-6 py-2 rounded-lg flex items-center gap-2 transition"
                    >
                        <RefreshCw size={18} className={isChecking ? 'animate-spin' : ''} />
                        {isChecking ? 'CHECKING...' : 'RE-SYNC'}
                    </button>
                </div>

                {/* Live Uplink Protocol */}
                <div className="bg-slate-900/50 rounded-lg p-6 mb-6">
                    <p className="text-slate-300 mb-4">Manual Uplink Override</p>
                    <div className="flex gap-3 mb-4">
                        <input 
                            type="text"
                            value={manualUrl}
                            onChange={(e) => setManualUrl(e.target.value)}
                            className="flex-1 bg-black/50 border border-slate-600 rounded px-3 py-2 text-cyan-400 font-mono text-sm"
                            placeholder="https://your-app.up.railway.app"
                        />
                        <button 
                            onClick={handleUrlUpdate}
                            className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded flex items-center gap-2 transition"
                        >
                            <Save size={16} /> SYNCHRONIZE
                        </button>
                    </div>
                    <p className="text-cyan-400 font-mono text-sm mb-4">TARGET: aurora-githubpages-production.up.railway.app</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-slate-800 rounded p-4">
                            <p className="text-slate-400 text-sm mb-1">Backend</p>
                            <p className={`text-lg font-bold ${status.backend === 'OPERATIONAL' ? 'text-green-400' : 'text-red-400'}`}>
                                {status.backend}
                            </p>
                        </div>
                        <div className="bg-slate-800 rounded p-4">
                            <p className="text-slate-400 text-sm mb-1">Persistence</p>
                            <p className={`text-lg font-bold ${status.database === 'SYNCHRONIZED' ? 'text-green-400' : 'text-yellow-400'}`}>
                                {status.database}
                            </p>
                        </div>
                        <div className="bg-slate-800 rounded p-4">
                            <p className="text-slate-400 text-sm mb-1">Spectral Engine</p>
                            <p className={`text-lg font-bold ${status.gee === 'KERNEL_ACTIVE' ? 'text-amber-400' : 'text-slate-400'}`}>
                                {status.gee}
                            </p>
                        </div>
                        <div className="bg-slate-800 rounded p-4">
                            <p className="text-slate-400 text-sm mb-1">Latency</p>
                            <p className="text-lg font-bold text-blue-400">{status.latency}</p>
                        </div>
                    </div>
                </div>

                {/* Infrastructure Status */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-slate-900/50 rounded-lg p-4">
                        <p className="text-slate-300 mb-2">Compute Node</p>
                        <p className="text-cyan-400 font-mono text-sm">Railway Cloud Platform</p>
                        <p className="text-green-400 text-sm mt-2">✓ SYNCHRONIZED</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-4">
                        <p className="text-slate-300 mb-2">Persistence</p>
                        <p className="text-cyan-400 font-mono text-sm">Neon Managed Storage</p>
                        <p className="text-green-400 text-sm mt-2">✓ OPERATIONAL</p>
                    </div>
                </div>
            </div>

            {/* Advanced Scanning Configuration */}
            <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-lg p-8 border border-purple-500/20 mb-8">
                <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                    <Search className="text-purple-400" size={28} />
                    Advanced Scanning Configuration
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {/* Scan Type */}
                    <div>
                        <label className="block text-sm font-semibold mb-2 flex items-center gap-2">
                            <Layers size={16} />
                            Scan Type
                        </label>
                        <select
                            value={scanConfig.scanType}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                scanType: e.target.value as any
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        >
                            <option value="point">Point Scan (Single Location)</option>
                            <option value="radius">Radius Scan (0-200km)</option>
                            <option value="grid">Grid Scan (Full Coverage)</option>
                        </select>
                    </div>

                    {/* Latitude */}
                    <div>
                        <label className="block text-sm font-semibold mb-2 flex items-center gap-2">
                            <MapPin size={16} />
                            Latitude
                        </label>
                        <input
                            type="number"
                            step="0.0001"
                            value={scanConfig.latitude}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                latitude: parseFloat(e.target.value)
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        />
                    </div>

                    {/* Longitude */}
                    <div>
                        <label className="block text-sm font-semibold mb-2 flex items-center gap-2">
                            <Globe size={16} />
                            Longitude
                        </label>
                        <input
                            type="number"
                            step="0.0001"
                            value={scanConfig.longitude}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                longitude: parseFloat(e.target.value)
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        />
                    </div>

                    {/* Country */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">Country</label>
                        <input
                            type="text"
                            value={scanConfig.country}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                country: e.target.value
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                            placeholder="e.g., Tanzania"
                        />
                    </div>

                    {/* Region */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">Region</label>
                        <input
                            type="text"
                            value={scanConfig.region}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                region: e.target.value
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                            placeholder="e.g., Tanzanian Craton"
                        />
                    </div>

                    {/* Radius (for radius scan) */}
                    {scanConfig.scanType === 'radius' && (
                        <div>
                            <label className="block text-sm font-semibold mb-2 flex items-center gap-2">
                                <Radio size={16} />
                                Radius (km): {scanConfig.radiusKm}
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="200"
                                step="5"
                                value={scanConfig.radiusKm}
                                onChange={(e) => setScanConfig(prev => ({
                                    ...prev,
                                    radiusKm: parseFloat(e.target.value)
                                }))}
                                className="w-full h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer"
                            />
                        </div>
                    )}

                    {/* Grid Spacing (for grid scan) */}
                    {scanConfig.scanType === 'grid' && (
                        <div>
                            <label className="block text-sm font-semibold mb-2">Grid Spacing (m)</label>
                            <input
                                type="number"
                                min="10"
                                max="1000"
                                step="10"
                                value={scanConfig.gridSpacingM}
                                onChange={(e) => setScanConfig(prev => ({
                                    ...prev,
                                    gridSpacingM: parseFloat(e.target.value)
                                }))}
                                className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                            />
                        </div>
                    )}

                    {/* Resolution */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">Resolution</label>
                        <select
                            value={scanConfig.resolution}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                resolution: e.target.value as any
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        >
                            <option value="native">Native (Pixel-by-Pixel)</option>
                            <option value="high">High (10m)</option>
                            <option value="medium">Medium (30m)</option>
                            <option value="low">Low (100m)</option>
                        </select>
                    </div>

                    {/* Sensor */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">Satellite Sensor</label>
                        <select
                            value={scanConfig.sensor}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                sensor: e.target.value
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        >
                            <option value="Sentinel-2">Sentinel-2 (10m, 5-day)</option>
                            <option value="Landsat-8">Landsat-8 (30m, 16-day)</option>
                        </select>
                    </div>

                    {/* Cloud Cover */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">Max Cloud Cover (%)</label>
                        <input
                            type="number"
                            min="0"
                            max="100"
                            step="5"
                            value={scanConfig.maxCloudCoverPercent}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                maxCloudCoverPercent: parseFloat(e.target.value)
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        />
                    </div>

                    {/* Date Start */}
                    <div>
                        <label className="block text-sm font-semibold mb-2 flex items-center gap-2">
                            <Clock size={16} />
                            Date Start (YYYY-MM-DD)
                        </label>
                        <input
                            type="date"
                            value={scanConfig.dateStart}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                dateStart: e.target.value
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        />
                    </div>

                    {/* Date End */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">Date End (YYYY-MM-DD)</label>
                        <input
                            type="date"
                            value={scanConfig.dateEnd}
                            onChange={(e) => setScanConfig(prev => ({
                                ...prev,
                                dateEnd: e.target.value
                            }))}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white"
                        />
                    </div>
                </div>

                {/* Mineral Selection */}
                <div className="mb-8">
                    <label className="block text-sm font-semibold mb-3">Minerals to Scan For</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                        {availableMinerals.map(mineral => (
                            <button
                                key={mineral}
                                onClick={() => handleMineralToggle(mineral)}
                                className={`px-4 py-2 rounded-lg font-semibold transition ${
                                    selectedMinerals.has(mineral)
                                        ? 'bg-purple-600 text-white border border-purple-400'
                                        : 'bg-slate-900 text-slate-300 border border-slate-600 hover:border-slate-500'
                                }`}
                            >
                                {mineral.toUpperCase()}
                            </button>
                        ))}
                    </div>
                    <p className="text-slate-400 text-sm mt-2">
                        Selected: {selectedMinerals.size > 0 ? Array.from(selectedMinerals).join(', ').toUpperCase() : 'None'}
                    </p>
                </div>

                {/* Start Scan Button */}
                <button
                    onClick={handleStartScan}
                    disabled={isScanning || selectedMinerals.size === 0}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg flex items-center justify-center gap-3 transition text-lg"
                >
                    <Search size={24} />
                    {isScanning ? 'SCANNING IN PROGRESS...' : 'START COMPREHENSIVE SCAN'}
                </button>
            </div>

            {/* Scan History */}
            {scanHistory.length > 0 && (
                <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-lg p-8 border border-blue-500/20 mb-8">
                    <h2 className="text-2xl font-bold flex items-center gap-3 mb-6">
                        <BarChart3 className="text-blue-400" size={28} />
                        Scan Repository
                    </h2>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                        {scanHistory.map((scan: any) => (
                            <div key={scan.scan_id} className="bg-slate-900/50 rounded p-4 flex justify-between items-start">
                                <div>
                                    <p className="font-mono text-cyan-400">{scan.scan_id}</p>
                                    <p className="text-sm text-slate-400 mt-1">{scan.location} • {scan.minerals?.join(', ')}</p>
                                    <p className="text-xs text-slate-500 mt-1">{scan.created_at}</p>
                                </div>
                                <div className="text-right">
                                    <p className={`text-sm font-bold ${
                                        scan.status === 'completed' ? 'text-green-400' :
                                        scan.status === 'running' ? 'text-yellow-400' :
                                        'text-blue-400'
                                    }`}>
                                        {scan.status.toUpperCase()}
                                    </p>
                                    {scan.detections_found && (
                                        <p className="text-xs text-slate-400 mt-1">{scan.detections_found} detections</p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Console Logs */}
            <div className="bg-slate-900 rounded-lg p-8 border border-slate-700">
                <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
                    <Terminal className="text-green-400" size={20} />
                    Infrastructure_Logs
                </h3>
                <div className="bg-black rounded p-4 font-mono text-sm text-green-400 max-h-64 overflow-y-auto">
                    {logs.length === 0 ? (
                        <p className="text-slate-500">Ready for diagnostics...</p>
                    ) : (
                        logs.map((log, i) => <div key={i}>{log}</div>)
                    )}
                </div>
            </div>
        </div>
    );
};

export default ConfigView;
