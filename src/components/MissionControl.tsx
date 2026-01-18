import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCw, CheckCircle, AlertCircle, Loader2, Database } from 'lucide-react';
import { AuroraAPI } from '../api';

interface ScanStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  error?: string;
  startTime?: Date;
  endTime?: Date;
}

interface ActiveScan {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  startTime: Date;
  steps: ScanStep[];
  overallProgress: number;
}

const MissionControl: React.FC = () => {
  const [activeScan, setActiveScan] = useState<ActiveScan | null>(null);
  const [latitude, setLatitude] = useState<string>('-9.5');
  const [longitude, setLongitude] = useState<string>('27.8');
  const [scanName, setScanName] = useState<string>('');
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [historicalScans, setHistoricalScans] = useState<any[]>([]);

  useEffect(() => {
    loadHistoricalScans();
  }, []);

  const loadHistoricalScans = async () => {
    try {
      const scans = await AuroraAPI.getAllScans();
      setHistoricalScans(scans || []);
    } catch (e) {
      console.error('Failed to load historical scans:', e);
    }
  };

  const startScan = async () => {
    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);

    if (isNaN(lat) || isNaN(lon)) {
      alert('Please enter valid coordinates');
      return;
    }

    const newScan: ActiveScan = {
      id: `scan-${Date.now()}`,
      name: scanName || `Scan ${new Date().toLocaleTimeString()}`,
      latitude: lat,
      longitude: lon,
      startTime: new Date(),
      steps: [
        { id: 'fetch-satellite', name: 'Fetch Satellite Data', status: 'pending', progress: 0 },
        { id: 'spectral-analysis', name: 'Spectral Analysis', status: 'pending', progress: 0 },
        { id: 'pinn-processing', name: 'PINN Processing', status: 'pending', progress: 0 },
        { id: 'ushe-harmonization', name: 'USHE Harmonization', status: 'pending', progress: 0 },
        { id: 'tmal-temporal', name: 'TMAL Temporal Analysis', status: 'pending', progress: 0 },
        { id: 'visualization', name: 'Generate Visualizations', status: 'pending', progress: 0 },
        { id: 'database-store', name: 'Store Results', status: 'pending', progress: 0 },
      ],
      overallProgress: 0,
    };

    setActiveScan(newScan);
    setIsRunning(true);

    // Run workflow
    await executeWorkflow(newScan);
  };

  const executeWorkflow = async (scan: ActiveScan) => {
    try {
      // Step 1: Fetch Satellite Data
      updateStep(scan.id, 'fetch-satellite', 'running', 0);
      const satelliteData = await AuroraAPI.fetchSatelliteData(scan.latitude, scan.longitude);
      if (!satelliteData || satelliteData.error) {
        updateStep(scan.id, 'fetch-satellite', 'error', 0, 'Failed to fetch satellite data - real data not available');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'fetch-satellite', 'completed', 100);
      updateOverallProgress(scan.id);

      // Step 2: Spectral Analysis
      updateStep(scan.id, 'spectral-analysis', 'running', 0);
      const spectralResults = await AuroraAPI.analyzeSpectralData(satelliteData);
      if (!spectralResults || spectralResults.error) {
        updateStep(scan.id, 'spectral-analysis', 'error', 0, 'Spectral analysis failed');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'spectral-analysis', 'completed', 100);
      updateOverallProgress(scan.id);

      // Step 3: PINN Processing
      updateStep(scan.id, 'pinn-processing', 'running', 0);
      const pinnResults = await AuroraAPI.runPINNAnalysis(scan.latitude, scan.longitude, satelliteData);
      if (!pinnResults || pinnResults.error) {
        updateStep(scan.id, 'pinn-processing', 'error', 0, 'PINN processing failed');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'pinn-processing', 'completed', 100);
      updateOverallProgress(scan.id);

      // Step 4: USHE Harmonization
      updateStep(scan.id, 'ushe-harmonization', 'running', 0);
      const usheResults = await AuroraAPI.runUSHEAnalysis(spectralResults);
      if (!usheResults || usheResults.error) {
        updateStep(scan.id, 'ushe-harmonization', 'error', 0, 'USHE harmonization failed');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'ushe-harmonization', 'completed', 100);
      updateOverallProgress(scan.id);

      // Step 5: TMAL Temporal Analysis
      updateStep(scan.id, 'tmal-temporal', 'running', 0);
      const tmalResults = await AuroraAPI.runTMALAnalysis(scan.latitude, scan.longitude);
      if (!tmalResults || tmalResults.error) {
        updateStep(scan.id, 'tmal-temporal', 'error', 0, 'TMAL analysis failed');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'tmal-temporal', 'completed', 100);
      updateOverallProgress(scan.id);

      // Step 6: Visualization Generation
      updateStep(scan.id, 'visualization', 'running', 0);
      const vizResults = await AuroraAPI.generateVisualizations({
        satellite: satelliteData,
        spectral: spectralResults,
        pinn: pinnResults,
        ushe: usheResults,
        tmal: tmalResults,
      });
      if (!vizResults || vizResults.error) {
        updateStep(scan.id, 'visualization', 'error', 0, 'Visualization generation failed');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'visualization', 'completed', 100);
      updateOverallProgress(scan.id);

      // Step 7: Store Results
      updateStep(scan.id, 'database-store', 'running', 0);
      const storeResult = await AuroraAPI.storeScanResults({
        scanId: scan.id,
        scanName: scan.name,
        latitude: scan.latitude,
        longitude: scan.longitude,
        timestamp: scan.startTime,
        satellite: satelliteData,
        spectral: spectralResults,
        pinn: pinnResults,
        ushe: usheResults,
        tmal: tmalResults,
        visualization: vizResults,
      });
      if (!storeResult || storeResult.error) {
        updateStep(scan.id, 'database-store', 'error', 0, 'Failed to store results');
        setIsRunning(false);
        return;
      }
      updateStep(scan.id, 'database-store', 'completed', 100);
      updateOverallProgress(scan.id);

      // Workflow complete
      setIsRunning(false);
      await loadHistoricalScans();
    } catch (e) {
      console.error('Workflow error:', e);
      setIsRunning(false);
    }
  };

  const updateStep = (scanId: string, stepId: string, status: ScanStep['status'], progress: number, error?: string) => {
    setActiveScan((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        steps: prev.steps.map((step) =>
          step.id === stepId ? { ...step, status, progress, error, startTime: new Date() } : step
        ),
      };
    });
  };

  const updateOverallProgress = (scanId: string) => {
    setActiveScan((prev) => {
      if (!prev) return null;
      const completed = prev.steps.filter((s) => s.status === 'completed').length;
      const total = prev.steps.length;
      return { ...prev, overallProgress: Math.round((completed / total) * 100) };
    });
  };

  return (
    <div className="w-full h-full bg-aurora-950 p-6 space-y-6 overflow-y-auto">
      {/* Mission Control Header */}
      <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6">
        <h1 className="text-2xl font-bold text-white mb-2">Mission Control</h1>
        <p className="text-slate-400 text-sm">Initiate and monitor comprehensive geological surveys</p>
      </div>

      {/* Scan Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <input
          type="text"
          placeholder="Scan Name"
          value={scanName}
          onChange={(e) => setScanName(e.target.value)}
          className="col-span-1 lg:col-span-2 px-4 py-3 bg-slate-900 border border-aurora-800 rounded text-white placeholder-slate-500 text-sm"
        />
        <input
          type="number"
          placeholder="Latitude"
          value={latitude}
          onChange={(e) => setLatitude(e.target.value)}
          step="0.01"
          className="px-4 py-3 bg-slate-900 border border-aurora-800 rounded text-white placeholder-slate-500 text-sm"
        />
        <input
          type="number"
          placeholder="Longitude"
          value={longitude}
          onChange={(e) => setLongitude(e.target.value)}
          step="0.01"
          className="px-4 py-3 bg-slate-900 border border-aurora-800 rounded text-white placeholder-slate-500 text-sm"
        />
        <button
          onClick={startScan}
          disabled={isRunning}
          className="col-span-1 lg:col-span-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-3 rounded flex items-center justify-center space-x-2 transition-colors"
        >
          <Play size={18} />
          <span>{isRunning ? 'SCANNING...' : 'START SCAN'}</span>
        </button>
      </div>

      {/* Active Scan */}
      {activeScan && (
        <div className="bg-aurora-900/30 border border-emerald-700 rounded-xl p-6">
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-bold text-emerald-400">{activeScan.name}</h2>
              <span className="text-sm text-slate-400">
                {activeScan.latitude.toFixed(4)}, {activeScan.longitude.toFixed(4)}
              </span>
            </div>
            <div className="w-full bg-slate-900 rounded h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-300"
                style={{ width: `${activeScan.overallProgress}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">{activeScan.overallProgress}% Complete</p>
          </div>

          {/* Steps */}
          <div className="space-y-2">
            {activeScan.steps.map((step) => (
              <div key={step.id} className="flex items-center space-x-3 p-3 bg-slate-950 rounded border border-slate-800">
                {step.status === 'pending' && <div className="w-5 h-5 rounded-full border-2 border-slate-600" />}
                {step.status === 'running' && <Loader2 size={20} className="text-aurora-400 animate-spin" />}
                {step.status === 'completed' && <CheckCircle size={20} className="text-emerald-500" />}
                {step.status === 'error' && <AlertCircle size={20} className="text-red-500" />}

                <div className="flex-1">
                  <p className="text-sm font-semibold text-white">{step.name}</p>
                  {step.error && <p className="text-xs text-red-400 mt-1">{step.error}</p>}
                </div>
                <span className="text-xs text-slate-400">{step.progress}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical Scans */}
      <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Database size={20} className="text-aurora-400" />
          <h3 className="text-lg font-bold text-white">Historical Scans</h3>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
          {historicalScans.length === 0 ? (
            <p className="text-slate-400 text-sm col-span-full">No scans yet. Start a new scan to begin.</p>
          ) : (
            historicalScans.map((scan) => (
              <div key={scan.id} className="bg-slate-950 border border-slate-800 rounded p-4">
                <p className="text-sm font-semibold text-white">{scan.scan_name}</p>
                <p className="text-xs text-slate-400 mt-1">
                  {scan.latitude.toFixed(4)}, {scan.longitude.toFixed(4)}
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  {new Date(scan.timestamp).toLocaleString()}
                </p>
                <div className="flex space-x-2 mt-3">
                  {scan.has_satellite && <span className="text-[10px] bg-blue-900/30 text-blue-300 px-2 py-1 rounded">Satellite</span>}
                  {scan.has_pinn && <span className="text-[10px] bg-purple-900/30 text-purple-300 px-2 py-1 rounded">PINN</span>}
                  {scan.has_ushe && <span className="text-[10px] bg-emerald-900/30 text-emerald-300 px-2 py-1 rounded">USHE</span>}
                  {scan.has_tmal && <span className="text-[10px] bg-orange-900/30 text-orange-300 px-2 py-1 rounded">TMAL</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default MissionControl;
