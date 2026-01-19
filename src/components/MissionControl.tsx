import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCw, CheckCircle, AlertCircle, Loader2, Database, ChevronUp, ChevronDown, X } from 'lucide-react';
import { AuroraAPI } from '../api';
import { MINERAL_DATABASE, getMineralsByCategory } from '../mineralDatabase';

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
  minerals: string[]; // mineral IDs
  startTime: Date;
  steps: ScanStep[];
  overallProgress: number;
}

interface MissionControlProps {
  onSetActiveScanLocation?: (lat: number, lon: number, name: string) => void;
  scrollToBottom?: () => void;
  activeScanLocation?: { lat: number; lon: number; name: string } | null;
}

const MissionControl: React.FC<MissionControlProps> = ({ onSetActiveScanLocation, scrollToBottom, activeScanLocation }) => {
  const [activeScan, setActiveScan] = useState<ActiveScan | null>(null);
  const [latitude, setLatitude] = useState<string>('-9.5');
  const [longitude, setLongitude] = useState<string>('27.8');
  const [scanName, setScanName] = useState<string>('');
  const [selectedMinerals, setSelectedMinerals] = useState<string[]>([]);
  const [showMineralPicker, setShowMineralPicker] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [historicalScans, setHistoricalScans] = useState<any[]>([]);
  const [showResultsDetails, setShowResultsDetails] = useState(false);

  // Get unique categories from mineral database
  const mineralCategories = React.useMemo(() => {
    const cats = new Map<string, string[]>();
    MINERAL_DATABASE.forEach((m) => {
      if (!cats.has(m.category)) {
        cats.set(m.category, []);
      }
      cats.get(m.category)?.push(m.id);
    });
    return cats;
  }, []);

  useEffect(() => {
    loadHistoricalScans();
  }, []);

  const loadHistoricalScans = async () => {
    try {
      const scans = await AuroraAPI.getAllScans();
      // Ensure scans is always an array
      if (Array.isArray(scans)) {
        setHistoricalScans(scans);
      } else {
        console.warn('Historical scans not in expected format:', scans);
        setHistoricalScans([]);
      }
    } catch (e) {
      console.error('Failed to load historical scans:', e);
      setHistoricalScans([]);
    }
  };

  const startScan = async () => {
    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);

    if (isNaN(lat) || isNaN(lon)) {
      alert('Please enter valid coordinates');
      return;
    }

    if (selectedMinerals.length === 0) {
      alert('Please select at least one mineral to scan for');
      return;
    }

    const mineralNames = selectedMinerals.map((id) => MINERAL_DATABASE.find((m) => m.id === id)?.name || id).join(', ');

    const newScan: ActiveScan = {
      id: `scan-${Date.now()}`,
      name: scanName || `Scan ${mineralNames}`,
      latitude: lat,
      longitude: lon,
      minerals: selectedMinerals,
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
    
    // Notify App of the active scan location
    if (onSetActiveScanLocation) {
      onSetActiveScanLocation(lat, lon, newScan.name);
    }

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
      // Save scan to history even if it failed
      await loadHistoricalScans();
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
    <div className="w-full h-full bg-aurora-950 p-6 space-y-4 overflow-y-auto">
      {/* Mission Control Header */}
      <div className="bg-aurora-900/50 border border-aurora-800 rounded-lg p-4">
        <h1 className="text-xl font-bold text-white">Mission Control</h1>
        <p className="text-slate-400 text-xs mt-1">Mineral-specific geological surveys with spectral analysis</p>
      </div>

      {/* Scan Parameters - Compact */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 space-y-3">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
          <input
            type="text"
            placeholder="Scan Name (optional)"
            value={scanName}
            onChange={(e) => setScanName(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded text-white placeholder-slate-500 text-xs"
          />
          <input
            type="number"
            placeholder="Latitude"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            step="0.01"
            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded text-white placeholder-slate-500 text-xs"
          />
          <input
            type="number"
            placeholder="Longitude"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            step="0.01"
            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded text-white placeholder-slate-500 text-xs"
          />
        </div>

        {/* Mineral Picker */}
        <div className="relative">
          <button
            onClick={() => setShowMineralPicker(!showMineralPicker)}
            className={`w-full px-3 py-2 text-xs font-mono rounded border transition-colors ${
              selectedMinerals.length > 0
                ? 'bg-emerald-900/30 border-emerald-700 text-emerald-300'
                : 'bg-slate-950 border-slate-700 text-slate-400'
            }`}
          >
            {selectedMinerals.length > 0
              ? `${selectedMinerals.length} mineral(s) selected`
              : 'Select Mineral(s) to Search For...'}
          </button>

          {showMineralPicker && (
            <div className="absolute z-50 top-full mt-1 w-full bg-slate-950 border border-slate-700 rounded shadow-xl max-h-96 overflow-y-auto">
              {Array.from(mineralCategories.entries()).map(([category, mineralIds]) => (
                <div key={category} className="border-b border-slate-800 last:border-b-0">
                  <div className="px-3 py-2 bg-slate-900/50 font-mono text-[10px] text-aurora-400 uppercase">
                    {category}
                  </div>
                  <div className="space-y-0.5 p-2">
                    {mineralIds.map((mineralId) => {
                      const mineral = MINERAL_DATABASE.find((m) => m.id === mineralId);
                      if (!mineral) return null;
                      const isSelected = selectedMinerals.includes(mineralId);
                      return (
                        <button
                          key={mineralId}
                          onClick={() => {
                            setSelectedMinerals((prev) =>
                              isSelected ? prev.filter((id) => id !== mineralId) : [...prev, mineralId]
                            );
                          }}
                          className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors ${
                            isSelected
                              ? 'bg-emerald-600 text-white'
                              : 'bg-slate-900 text-slate-300 hover:bg-slate-800'
                          }`}
                        >
                          <span className="font-mono text-[10px]">{mineral.symbol}</span>
                          <span className="ml-2">{mineral.name}</span>
                          {mineral.subtype && (
                            <span className="text-[9px] ml-1 text-slate-400">({mineral.subtype})</span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Minerals Display */}
        {selectedMinerals.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {selectedMinerals.map((mineralId) => {
              const mineral = MINERAL_DATABASE.find((m) => m.id === mineralId);
              if (!mineral) return null;
              return (
                <div
                  key={mineralId}
                  className="flex items-center space-x-1 px-2 py-1 bg-emerald-900/30 border border-emerald-700 rounded text-[10px] text-emerald-300"
                >
                  <span className="font-mono">{mineral.symbol}</span>
                  <button
                    onClick={() =>
                      setSelectedMinerals((prev) => prev.filter((id) => id !== mineralId))
                    }
                    className="hover:text-emerald-100"
                  >
                    <X size={12} />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Start Scan Button */}
        <button
          onClick={startScan}
          disabled={isRunning || selectedMinerals.length === 0}
          className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-2 px-4 rounded text-sm flex items-center justify-center space-x-2 transition-colors"
        >
          <Play size={16} />
          <span>{isRunning ? 'SCANNING...' : 'START SCAN'}</span>
        </button>
      </div>

      {/* Active Scan - Compact Terminal Style */}
      {activeScan && (
        <div className="bg-black border-2 border-blue-600 rounded-lg p-3 font-mono text-xs overflow-hidden">
          {/* Header */}
          <div className="text-blue-400 mb-2 pb-2 border-b border-blue-600">
            <div>
              <span className="text-green-400">$</span> AURORA_SCAN <span className="text-cyan-300">{activeScan.name}</span>
            </div>
            <div className="text-slate-500 mt-1">
              Location: {activeScan.latitude.toFixed(4)}°, {activeScan.longitude.toFixed(4)}°
            </div>
            <div className="text-slate-500">
              Minerals: {activeScan.minerals.map((id) => MINERAL_DATABASE.find((m) => m.id === id)?.symbol).join(', ')}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-2">
            <div className="flex justify-between text-slate-400 mb-1">
              <span>Progress</span>
              <span>{activeScan.overallProgress}%</span>
            </div>
            <div className="w-full bg-slate-950 border border-slate-700 h-2 rounded">
              <div
                className={`h-full transition-all duration-300 ${
                  activeScan.overallProgress === 100
                    ? 'bg-green-500'
                    : activeScan.overallProgress > 50
                      ? 'bg-cyan-500'
                      : 'bg-yellow-500'
                }`}
                style={{ width: `${activeScan.overallProgress}%` }}
              />
            </div>
          </div>

          {/* Steps - Compact Terminal Output */}
          <div className="space-y-1 max-h-48 overflow-y-auto mb-2 bg-black p-2 border border-slate-800 rounded">
            {activeScan.steps.map((step) => (
              <div key={step.id} className="flex items-center space-x-2">
                {step.status === 'pending' && <span className="text-slate-600">[ ]</span>}
                {step.status === 'running' && <span className="text-cyan-400 animate-pulse">[→]</span>}
                {step.status === 'completed' && <span className="text-green-400">[✓]</span>}
                {step.status === 'error' && <span className="text-red-500">[✗]</span>}
                <span className={`${
                  step.status === 'completed' ? 'text-green-400' :
                  step.status === 'running' ? 'text-cyan-300' :
                  step.status === 'error' ? 'text-red-400' :
                  'text-slate-500'
                }`}>
                  {step.name}
                </span>
                {step.status === 'running' && <span className="text-slate-500 ml-auto">{step.progress}%</span>}
                {step.error && <span className="text-red-500 ml-auto text-[10px]">{step.error}</span>}
              </div>
            ))}
          </div>

          {/* Results Summary - Expandable */}
          {activeScan.overallProgress === 100 && (
            <div className="mt-2 pt-2 border-t border-blue-600">
              <button
                onClick={() => setShowResultsDetails(!showResultsDetails)}
                className="w-full text-left px-2 py-1 hover:bg-slate-900 rounded text-green-400"
              >
                <span>{showResultsDetails ? '▼' : '▶'}</span>
                <span className="ml-2">SCAN COMPLETE - Results Available</span>
              </button>
              
              {showResultsDetails && (
                <div className="mt-2 pt-2 border-t border-slate-700 text-slate-300 space-y-1 text-[10px]">
                  <div>✓ All 7 analysis steps completed successfully</div>
                  <div>✓ Results stored to database</div>
                  <div>→ View in Historical Scans or export data</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Historical Scans */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Database size={16} className="text-aurora-400" />
          <h3 className="font-bold text-white text-sm">Historical Scans</h3>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
          {historicalScans.length === 0 ? (
            <p className="text-slate-400 text-xs col-span-full">No scans yet. Start a new scan to begin.</p>
          ) : (
            historicalScans.map((scan) => (
              <div 
                key={scan.id} 
                onClick={() => {
                  if (onSetActiveScanLocation) {
                    onSetActiveScanLocation(scan.latitude, scan.longitude, scan.scan_name);
                  }
                }}
                className="bg-slate-950 border border-slate-700 rounded p-2 cursor-pointer hover:border-aurora-500 hover:bg-slate-900 transition-colors"
              >
                <p className="text-xs font-semibold text-white">{scan.scan_name}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {scan.latitude.toFixed(4)}°, {scan.longitude.toFixed(4)}°
                </p>
                <p className="text-[9px] text-slate-500 mt-1">
                  {new Date(scan.timestamp).toLocaleString()}
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {scan.has_satellite && <span className="text-[8px] bg-blue-900/50 text-blue-300 px-1.5 py-0.5 rounded">Sat</span>}
                  {scan.has_pinn && <span className="text-[8px] bg-purple-900/50 text-purple-300 px-1.5 py-0.5 rounded">PINN</span>}
                  {scan.has_ushe && <span className="text-[8px] bg-emerald-900/50 text-emerald-300 px-1.5 py-0.5 rounded">USHE</span>}
                  {scan.has_tmal && <span className="text-[8px] bg-orange-900/50 text-orange-300 px-1.5 py-0.5 rounded">TMAL</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Scroll Navigation */}
      <div className="fixed bottom-6 right-6 space-y-2 z-50">
        <button
          onClick={scrollToTop}
          className="w-10 h-10 bg-aurora-600 hover:bg-aurora-500 rounded-full flex items-center justify-center transition-colors shadow-lg"
          title="Scroll to Top"
        >
          <ChevronUp size={16} className="text-white" />
        </button>
        <button
          onClick={scrollToBottom}
          className="w-10 h-10 bg-aurora-600 hover:bg-aurora-500 rounded-full flex items-center justify-center transition-colors shadow-lg"
          title="Scroll to Bottom"
        >
          <ChevronDown size={16} className="text-white" />
        </button>
      </div>
    </div>
  );
};

export default MissionControl;
