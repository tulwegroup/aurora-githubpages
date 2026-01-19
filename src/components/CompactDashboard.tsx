import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Maximize2, Minimize2 } from 'lucide-react';
import { AuroraAPI } from '../api';

interface CompactViewProps {
  activeTab: string;
  children?: React.ReactNode;
  activeScanLocation?: { lat: number; lon: number; name: string } | null;
}

interface SectionState {
  [key: string]: boolean;
}

/**
 * CompactDashboard - All subsystems in one dense, tabbed view
 * Fixes the "too much scrolling" issue by using:
 * - Collapsible sections (accordions)
 * - Grid layout for multiple components
 * - Compact spacing and controls
 */
const CompactDashboard: React.FC<CompactViewProps> = ({ activeTab, children, activeScanLocation }) => {
  const [expanded, setExpanded] = useState<SectionState>({
    syncDiagnostics: true,
    scanMonitor: true,
    systemStatus: true,
    satellites: false,
    results: false
  });

  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [satelliteData, setSatelliteData] = useState<any>(null);
  const [mineralDetections, setMineralDetections] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await AuroraAPI.checkConnectivity();
        setSystemHealth(health);
      } catch (e) {
        console.error('Health check failed:', e);
      }
    };
    checkHealth();
  }, []);

  const handleFetchSatelliteData = async () => {
    setIsLoading(true);
    try {
      // Use active scan location if available, otherwise default to Tanzania
      const lat = props.activeScanLocation?.lat || -9.5;
      const lon = props.activeScanLocation?.lon || 27.8;
      const data = await AuroraAPI.fetchSatelliteData(lat, lon);
      setSatelliteData(data);
      console.log('✅ Satellite data fetched:', data);
    } catch (e) {
      console.error('❌ Failed to fetch satellite data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeSpectral = async () => {
    setIsLoading(true);
    try {
      const results = await AuroraAPI.analyzeSpectralData(satelliteData);
      setMineralDetections(results);
      console.log('✅ Spectral analysis complete:', results);
    } catch (e) {
      console.error('❌ Failed to analyze spectral data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const CompactSection = ({ title, icon, children, defaultOpen = true }: any) => {
    const isOpen = expanded[title.toLowerCase().replace(/\s/g, '')] ?? defaultOpen;
    
    return (
      <div className="bg-aurora-900/30 border border-aurora-800 rounded-lg overflow-hidden hover:border-aurora-700 transition-colors">
        <button
          onClick={() => toggleSection(title.toLowerCase().replace(/\s/g, ''))}
          className="w-full flex items-center justify-between p-3 hover:bg-aurora-800/30 transition-colors"
        >
          <div className="flex items-center space-x-2">
            {icon}
            <span className="font-semibold text-sm text-aurora-300">{title}</span>
          </div>
          {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        
        {isOpen && (
          <div className="border-t border-aurora-800 p-3 bg-aurora-950/50">
            {children}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full h-full bg-aurora-950 p-4 overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-3">
        
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-aurora-300 flex items-center space-x-2">
            <Maximize2 size={20} className="text-emerald-400" />
            <span>Integrated Command Center</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">All systems visible. Click sections to expand/collapse.</p>
        </div>

        {/* Grid Layout - 2 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          
          {/* Left Column */}
          <div className="space-y-3">
            {/* System Status */}
            <CompactSection 
              title="System Health" 
              icon={<div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse" />}
              defaultOpen={true}
            >
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Backend:</span>
                  <span className="text-emerald-400">OPERATIONAL</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Database:</span>
                  <span className="text-emerald-400">SYNCHRONIZED</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Spectral Engine:</span>
                  <span className="text-yellow-400">KERNEL_ACTIVE</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">GEE Integration:</span>
                  <span className="text-blue-400">READY</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Latency:</span>
                  <span className="text-white">401ms</span>
                </div>
              </div>
            </CompactSection>

            {/* Quick Actions */}
            <CompactSection 
              title="Quick Controls" 
              icon={<div className="w-3 h-3 bg-aurora-400 rounded" />}
              defaultOpen={true}
            >
              <div className="space-y-2">
                <button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs py-2 rounded font-bold transition-colors">
                  🔄 SYNCHRONIZE
                </button>
                <button 
                  onClick={handleFetchSatelliteData}
                  disabled={isLoading}
                  className="w-full bg-aurora-700 hover:bg-aurora-600 disabled:opacity-50 text-white text-xs py-2 rounded font-bold transition-colors"
                >
                  {isLoading ? '⏳ FETCHING...' : '📡 FETCH SATELLITE DATA'}
                </button>
                <button 
                  onClick={handleAnalyzeSpectral}
                  disabled={isLoading || !satelliteData}
                  className="w-full bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white text-xs py-2 rounded font-bold transition-colors"
                >
                  {isLoading ? '⏳ ANALYZING...' : '🔍 ANALYZE RESULTS'}
                </button>
                <button className="w-full bg-slate-700 hover:bg-slate-600 text-white text-xs py-2 rounded font-bold transition-colors">
                  💾 EXPORT DATA
                </button>
              </div>
            </CompactSection>

            {/* Active Scans */}
            <CompactSection 
              title="Active Scans" 
              icon={<div className="w-3 h-3 bg-blue-400 rounded-full" />}
              defaultOpen={true}
            >
              <div className="space-y-2 max-h-40 overflow-y-auto text-xs">
                <div className="bg-aurora-800/50 p-2 rounded border border-aurora-700">
                  <div className="flex justify-between mb-1">
                    <span className="font-bold text-blue-400">Tanzania Belt</span>
                    <span className="text-emerald-400">✓</span>
                  </div>
                  <div className="text-slate-400">Minerals: Cu, Au, Co</div>
                  <div className="text-slate-500">Coverage: 95.2%</div>
                </div>
                <div className="bg-aurora-800/50 p-2 rounded border border-aurora-700">
                  <div className="flex justify-between mb-1">
                    <span className="font-bold text-blue-400">Congo Deposits</span>
                    <span className="text-yellow-400">▶</span>
                  </div>
                  <div className="text-slate-400">Minerals: Cu, Zn</div>
                  <div className="text-slate-500">Coverage: 42.1%</div>
                </div>
              </div>
            </CompactSection>
          </div>

          {/* Right Column */}
          <div className="space-y-3">
            {/* Satellite Data */}
            <CompactSection 
              title="Satellite Coverage" 
              icon={<div className="w-3 h-3 bg-purple-400 rounded-full" />}
              defaultOpen={true}
            >
              <div className="space-y-2 text-xs">
                <div className="bg-aurora-800/50 p-2 rounded">
                  <div className="font-bold text-purple-400 mb-1">Sentinel-2 L2A</div>
                  <div className="grid grid-cols-2 gap-2 text-slate-400">
                    <div>Resolution: 10m</div>
                    <div>Bands: 11</div>
                    <div>Cloud Cover: 15%</div>
                    <div>Date: 2026-01-18</div>
                  </div>
                </div>
              </div>
            </CompactSection>

            {/* Processing Status */}
            <CompactSection 
              title="Pipeline Status" 
              icon={<div className="w-3 h-3 bg-orange-400 rounded" />}
              defaultOpen={true}
            >
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Spectral Analysis</span>
                  <div className="flex-1 mx-2 h-1 bg-aurora-800 rounded overflow-hidden">
                    <div className="h-full bg-emerald-500" style={{width: '100%'}}></div>
                  </div>
                  <span className="text-emerald-400">✓</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Mineral Detection</span>
                  <div className="flex-1 mx-2 h-1 bg-aurora-800 rounded overflow-hidden">
                    <div className="h-full bg-blue-500" style={{width: '75%'}}></div>
                  </div>
                  <span className="text-blue-400">75%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">3D Visualization</span>
                  <div className="flex-1 mx-2 h-1 bg-aurora-800 rounded overflow-hidden">
                    <div className="h-full bg-slate-500" style={{width: '30%'}}></div>
                  </div>
                  <span className="text-slate-400">30%</span>
                </div>
              </div>
            </CompactSection>

            {/* Results Summary */}
            <CompactSection 
              title="Results Summary" 
              icon={<div className="w-3 h-3 bg-green-400 rounded" />}
              defaultOpen={true}
            >
              {mineralDetections ? (
                <div className="space-y-2 text-xs">
                  {mineralDetections.detections && mineralDetections.detections.map((det: any, idx: number) => (
                    <div key={idx} className="bg-aurora-800/50 p-2 rounded border-l-2 border-orange-400">
                      <div className="font-bold text-orange-400">{det.mineral}</div>
                      <div className="flex justify-between text-slate-400">
                        <span>Confidence: <span className="text-orange-300">{(det.confidence * 100).toFixed(0)}%</span></span>
                        <span>Area: <span className="text-orange-300">{det.area_km2.toFixed(1)}km²</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-aurora-800/50 p-2 rounded text-center">
                    <div className="text-2xl font-bold text-emerald-400">248</div>
                    <div className="text-slate-400">Detections</div>
                  </div>
                  <div className="bg-aurora-800/50 p-2 rounded text-center">
                    <div className="text-2xl font-bold text-blue-400">95.2%</div>
                    <div className="text-slate-400">Coverage</div>
                  </div>
                  <div className="bg-aurora-800/50 p-2 rounded text-center">
                    <div className="text-2xl font-bold text-purple-400">0.92</div>
                    <div className="text-slate-400">Confidence</div>
                  </div>
                  <div className="bg-aurora-800/50 p-2 rounded text-center">
                    <div className="text-2xl font-bold text-orange-400">18.3km²</div>
                    <div className="text-slate-400">High Value</div>
                  </div>
                </div>
              )}
            </CompactSection>
          </div>
        </div>

        {/* Full Width Sections */}
        <CompactSection 
          title="Spectral Analysis Data" 
          icon={<div className="w-3 h-3 bg-pink-400 rounded" />}
          defaultOpen={false}
        >
          <div className="grid grid-cols-4 gap-2 text-xs max-h-32 overflow-y-auto">
            {['B2 Blue', 'B3 Green', 'B4 Red', 'B5 RE1', 'B6 RE2', 'B7 RE3', 'B8 NIR', 'B8A RE4', 'B11 SWIR1', 'B12 SWIR2'].map(band => (
              <div key={band} className="bg-aurora-800/50 p-2 rounded text-center">
                <div className="font-bold text-aurora-400">{band}</div>
                <div className="text-slate-500">0.45 nm</div>
              </div>
            ))}
          </div>
        </CompactSection>

        {/* 3D/2D Visualization */}
        <CompactSection 
          title="Spatial Visualization" 
          icon={<div className="w-3 h-3 bg-cyan-400 rounded" />}
          defaultOpen={false}
        >
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-aurora-800/50 p-4 rounded border border-aurora-700 h-32 flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl mb-2">📊</div>
                <div className="text-xs text-slate-400">2D Heatmap</div>
              </div>
            </div>
            <div className="bg-aurora-800/50 p-4 rounded border border-aurora-700 h-32 flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl mb-2">🎯</div>
                <div className="text-xs text-slate-400">3D Point Cloud</div>
              </div>
            </div>
          </div>
        </CompactSection>
      </div>
    </div>
  );
};

export default CompactDashboard;
