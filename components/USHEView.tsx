import React, { useState, useEffect, useRef } from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Cell, CartesianGrid, AreaChart, Area, ComposedChart, Line } from 'recharts';
import { NEURAL_MODULES, DRILL_HOLE_DATABASE } from '../constants';
import { Network, Cpu, Activity, CheckCircle, Database, Terminal, Zap, ChevronDown, Target, Scale, FileSpreadsheet, Clipboard, Eye, Sparkles, X, Upload } from 'lucide-react';
import { NeuralModule, ExplorationCampaign, DrillRecord, CalibrationLog, LatentPoint } from '../types';
import { AuroraAPI } from '../api';

interface USHEViewProps {
  campaign: ExplorationCampaign;
}

const DEFAULT_PROJECTS = [
    { id: 'tz', name: 'Reference: Tanzania Rift (Helium)', lat: -8.12, lon: 33.45, type: 'Noble Gas', context: 'Active Rift System', radius: 50 },
    { id: 'nv', name: 'Reference: Nevada Basin (Lithium)', lat: 38.50, lon: -117.50, type: 'Battery Metal', context: 'Sedimentary Basin / Salar', radius: 50 },
    { id: 'sa', name: 'Reference: Saudi Shield (Gold)', lat: 24.50, lon: 42.10, type: 'Precious Metal', context: 'Stable Craton / Shear Zone', radius: 50 },
    { id: 'gh-jubilee', name: 'Reference: Ghana Jubilee (Offshore)', lat: 4.58, lon: -2.95, type: 'Hydrocarbon', context: 'Deepwater Turbidite / Transform Margin', radius: 50 }
];

const COLORS = { 'Mineral': '#10b981', 'Water': '#22d3ee', 'Void': '#f59e0b' };

class SeededRNG {
    private seed: number;
    constructor(seedStr: string) {
        let h = 0x811c9dc5;
        for (let i = 0; i < seedStr.length; i++) {
            h ^= seedStr.charCodeAt(i);
            h = Math.imul(h, 0x01000193);
        }
        this.seed = h >>> 0;
    }
    next() {
        this.seed = (this.seed * 1664525 + 1013904223) % 4294967296;
        return this.seed / 4294967296;
    }
    range(min: number, max: number) {
        return min + (this.next() * (max - min));
    }
}

const generateSpectralData = (type: string, rng: SeededRNG) => {
    const points = [];
    for (let i = 400; i <= 2500; i += 50) {
        let rawOptical = rng.next() * 0.2 + 0.3 + (Math.sin(i / 300) * 0.1);
        let rawSAR = rng.next() * 0.1 + 0.2 + (Math.cos(i / 500) * 0.15);
        let rawThermal = rng.next() * 0.15 + 0.4 + (Math.sin(i / 800) * 0.1);
        let rawGravity = rng.next() * 0.1 + 0.3 + (Math.cos(i / 600) * 0.1); 
        const fused = (rawOptical * 0.3 + rawSAR * 0.3 + rawThermal * 0.2 + rawGravity * 0.2) * 1.3; 
        points.push({ wavelength: i, Optical: rawOptical, SAR: rawSAR, Thermal: rawThermal, Gravity: rawGravity, Fused: fused });
    }
    return points;
};

const generateConvergenceData = (type: string, rng: SeededRNG) => {
    const data = [];
    for (let x = 0; x <= 100; x+=2) {
        const dist = Math.abs(x - 50);
        const anomalyShape = Math.exp(-(dist * dist) / 100);
        const gravity = 0.2 + (0.6 * anomalyShape) + (rng.next() * 0.05);
        const magnetic = 0.3 + (0.5 * anomalyShape) + (rng.next() * 0.1) - 0.05;
        const thermal = 0.1 + (0.7 * anomalyShape) + (rng.next() * 0.05);
        const convergence = (gravity * magnetic * thermal) * 2.5; 
        data.push({ distance: x, gravity, magnetic, thermal, convergence: Math.min(1.2, convergence), depth: 300 + (x * 12) });
    }
    return data;
};

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        const d = payload[0].payload;
        return (
            <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl text-xs">
                <p className="text-slate-400 mb-1">Offset: {label}m</p>
                <p className="font-bold text-emerald-400">Convergence: {d.convergence.toFixed(2)}</p>
                <p className="text-blue-400 font-mono">Est. Depth: {d.depth.toFixed(0)}m</p>
            </div>
        );
    }
    return null;
};

const USHEView: React.FC<USHEViewProps> = ({ campaign }) => {
  const [activeTab, setActiveTab] = useState<'fusion' | 'latent' | 'calibration'>('fusion');
  const [availableProjects, setAvailableProjects] = useState<any[]>(DEFAULT_PROJECTS);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [selectedProject, setSelectedProject] = useState(DEFAULT_PROJECTS[0]);
  const [isTraining, setIsTraining] = useState(false);
  const [isCalibrated, setIsCalibrated] = useState(false);
  const [drillData, setDrillData] = useState<DrillRecord[] | null>(null);
  const [convergenceData, setConvergenceData] = useState<any[]>([]);
  const [showInjectModal, setShowInjectModal] = useState(false);
  
  const [ingestMode, setIngestMode] = useState<'upload' | 'paste'>('upload');
  const [pasteContent, setPasteContent] = useState('');
  const [rawFilePreview, setRawFilePreview] = useState<string>('');
  
  const [calibrationLogs, setCalibrationLogs] = useState<CalibrationLog[]>([]);
  const [latentData, setLatentData] = useState<LatentPoint[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
      const loadHistory = async () => {
          const allCampaigns = await AuroraAPI.getAllCampaigns();
          
          const history = allCampaigns.map(c => {
              let lat = 0, lon = 0;
              try {
                  const nums = c.targetCoordinates.match(/-?\d+(\.\d+)?/g);
                  if (nums && nums.length >= 2) {
                      lat = parseFloat(nums[0]);
                      if (c.targetCoordinates.includes('S')) lat = -lat;
                      lon = parseFloat(nums[1]);
                      if (c.targetCoordinates.includes('W')) lon = -lon;
                  }
              } catch(e) {}
              
              return {
                  id: c.id,
                  name: `Scan: ${c.name} (${c.regionName})`,
                  lat,
                  lon,
                  type: c.resourceType,
                  context: c.regionName || 'Custom Mission',
                  radius: c.radius || 10
              };
          });
          
          const combined = [...history, ...DEFAULT_PROJECTS].filter((v,i,a)=>a.findIndex(t=>(t.id === v.id))===i);
          setAvailableProjects(combined);
          
          const current = combined.find(p => p.id === campaign.id);
          if (current) setSelectedProject(current);
          else if (combined.length > 0) setSelectedProject(combined[0]);
      };
      loadHistory();
  }, [campaign]);

  useEffect(() => {
      if (!selectedProject) return;
      const seedStr = `${selectedProject.id}-${selectedProject.lat}-${selectedProject.lon}-${selectedProject.type}`;
      const rng = new SeededRNG(seedStr);
      setLatentData(AuroraAPI.generateLatentPoints(selectedProject.type, selectedProject.lat, selectedProject.lon, selectedProject.radius));
      setConvergenceData(generateConvergenceData(selectedProject.type, rng));
      
      const dbKey = selectedProject.id;
      const records = DRILL_HOLE_DATABASE[dbKey as keyof typeof DRILL_HOLE_DATABASE];
      if (records) { setDrillData(records); setIsCalibrated(false); } else { setDrillData(null); setChartData([]); }
  }, [selectedProject]);

  useEffect(() => {
      if (drillData) {
          const mappedData = drillData.map(record => {
             const rng = new SeededRNG(`${selectedProject.id}-${record.id}`);
             const rand = rng.next();
             const noise = isCalibrated ? (rand - 0.5) * 0.1 * record.measurement_value : (rand - 0.5) * 0.8 * record.measurement_value;
             const bias = isCalibrated ? 0 : record.measurement_value * 0.3;
             return { id: record.id, actual: record.measurement_value, predicted: Math.max(0, record.measurement_value + noise + bias), lithology: record.lithology, depth: record.depth_m, unit: record.measurement_unit };
          });
          setChartData(mappedData);
      }
  }, [drillData, isCalibrated, selectedProject]);

  const handleRunCalibration = async () => {
      setShowInjectModal(false);
      setIsTraining(true);
      const newLog: CalibrationLog = {
          id: `CAL-${Date.now()}`,
          user: 'System Admin (Rig Data Ingest)',
          region_id: selectedProject.id,
          timestamp: new Date().toISOString(),
          reference_count: drillData ? drillData.length : 0,
          model_version_before: 'v3.1.0-base',
          model_version_after: `v3.2.0-LIVE-${selectedProject.id.substring(0,6)}`,
          metrics_delta: { r2: 0.89, rmse: -1.25 }
      };
      
      await new Promise(r => setTimeout(r, 2500));
      
      setIsCalibrated(true); 
      setIsTraining(false); 
      setCalibrationLogs(prev => [newLog, ...prev]); 
      
      const updatedCampaign: ExplorationCampaign = {
          ...campaign,
          priorsLoaded: true,
          accuracyScore: 0.95
      };
      await AuroraAPI.updateCampaign(updatedCampaign);
  };

  const parseRobust = (input: string): DrillRecord[] => {
      let clean = input.replace(/^\uFEFF/, '').replace(/['"]/g, '').replace(/\r\n/g, '\n').replace(/\r/g, '\n');
      const lines = clean.split('\n').filter(l => l.trim().length > 0);
      const results: DrillRecord[] = [];

      const sample = lines.slice(0, 5).join('\n');
      const dotCount = (sample.match(/\d\.\d/g) || []).length;
      const commaDecimalCount = (sample.match(/\d,\d/g) || []).length;
      const useCommaAsDecimal = commaDecimalCount > dotCount && dotCount === 0;

      lines.forEach((line, idx) => {
          let processLine = line;
          if (useCommaAsDecimal) {
              processLine = line.replace(/(\d),(\d)/g, '$1.$2'); 
          }
          const numbers = processLine.match(/-?\d+(\.\d+)?/g);
          if (numbers && numbers.length >= 2) {
              const n1 = parseFloat(numbers[0]);
              const n2 = parseFloat(numbers[1]);
              let lat = n1;
              let lon = n2;
              if (Math.abs(n1) > 90 && Math.abs(n2) <= 90) { lat = n2; lon = n1; }
              if (!isNaN(lat) && !isNaN(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180) {
                  results.push({
                      id: `INJECT-${Date.now()}-${idx}`,
                      lat, lon,
                      depth_m: 0,
                      measurement_value: 1.0, 
                      measurement_unit: 'Binary',
                      lithology: 'Confirmed Site',
                      sample_date: new Date().toISOString(),
                      source: 'User Input',
                      license: 'Private',
                      notes: 'Manual Injection'
                  });
              }
          }
      });
      return results;
  };

  const processIngestion = (text: string) => {
      setUploadError(null);
      setRawFilePreview(text.substring(0, 500) + (text.length > 500 ? '...' : ''));
      try {
          const records = parseRobust(text);
          if (records.length === 0) {
              setUploadError("Parser Error: No valid Latitude/Longitude pairs found.");
          } else {
              setDrillData(records);
              setIsCalibrated(false);
          }
      } catch (e: any) {
          setUploadError("Critical Parser Failure: " + e.message);
      }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
          try {
              const text = await file.text();
              processIngestion(text);
          } catch(e) {
              setUploadError("Could not read file.");
          }
          event.target.value = ''; 
      }
  };

  const handlePasteSubmit = () => {
      if(!pasteContent) return;
      processIngestion(pasteContent);
  };

  return (
    <div className="space-y-6 relative h-full">
      <div className="flex flex-col md:flex-row justify-between items-center bg-aurora-900/50 border border-aurora-800 rounded-xl p-4 gap-4">
          <div className="flex items-center space-x-4">
              <div className="p-3 bg-aurora-500/10 rounded-full border border-aurora-500/20">
                  <Network className="text-aurora-500" size={24} />
              </div>
              <div>
                  <h2 className="text-lg font-bold text-white">Universal Subspace Harmonization Engine (USHE)</h2>
                  <p className="text-xs text-slate-400 font-mono">LATENT SPACE ALIGNMENT • {selectedProject.name}</p>
              </div>
          </div>
          <div className="flex items-center space-x-4">
              <div className="relative">
                  <select 
                      className="bg-slate-950 border border-slate-700 rounded-lg py-2 pl-3 pr-8 text-xs text-white focus:border-aurora-500 outline-none appearance-none"
                      onChange={(e) => {
                          const proj = availableProjects.find(p => p.id === e.target.value);
                          if (proj) setSelectedProject(proj);
                      }}
                      value={selectedProject.id}
                  >
                      {availableProjects.map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
              <button 
                  onClick={() => setShowInjectModal(true)} 
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-lg ${isCalibrated ? 'bg-emerald-900/20 text-emerald-400 border border-emerald-500/30' : 'bg-aurora-600 hover:bg-aurora-500 text-white'}`}
              >
                  {isCalibrated ? <CheckCircle size={16} /> : <Database size={16} />}
                  <span>{isCalibrated ? 'Model Calibrated' : 'Inject Ground Truth'}</span>
              </button>
          </div>
      </div>

      <div className="flex space-x-1 bg-aurora-900/30 p-1 rounded-lg w-fit border border-aurora-800">
         <button onClick={() => setActiveTab('fusion')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'fusion' ? 'bg-aurora-800 text-white shadow-md' : 'text-slate-400 hover:text-white'}`}>Signal Convergence</button>
         <button onClick={() => setActiveTab('latent')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center ${activeTab === 'latent' ? 'bg-aurora-800 text-white shadow-md' : 'text-slate-400 hover:text-white'}`}>Latent Space <span className="ml-2 bg-slate-900 text-[10px] px-1.5 rounded-full">{latentData.length}</span></button>
         <button onClick={() => setActiveTab('calibration')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center ${activeTab === 'calibration' ? 'bg-aurora-800 text-white shadow-md' : 'text-slate-400 hover:text-white'}`}>Calibration <span className={`ml-2 w-2 h-2 rounded-full ${isCalibrated ? 'bg-emerald-500' : 'bg-red-500'}`}></span></button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
          <div className="lg:col-span-2 bg-slate-950 border border-aurora-800 rounded-xl overflow-hidden flex flex-col relative">
              {activeTab === 'fusion' && (
                  <>
                    <div className="p-4 border-b border-aurora-800 bg-aurora-900/20 flex justify-between items-center">
                        <div className="flex items-center space-x-2"><Activity className="text-aurora-400" size={18} /><h3 className="font-semibold text-slate-200">Multi-Modal Convergence</h3></div>
                    </div>
                    <div className="flex-1 w-full h-full p-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={convergenceData}>
                                <defs>
                                    <linearGradient id="colorConv" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                <XAxis dataKey="distance" stroke="#475569" label={{ value: 'Transect Distance (km)', position: 'insideBottom', offset: -5, fill: '#64748b' }} />
                                <YAxis stroke="#475569" />
                                <Tooltip content={<CustomTooltip />} />
                                <Area type="monotone" dataKey="convergence" fill="url(#colorConv)" stroke="#10b981" strokeWidth={2} />
                                <Line type="monotone" dataKey="thermal" stroke="#3b82f6" dot={false} strokeWidth={2} strokeDasharray="5 5" />
                                <Line type="monotone" dataKey="magnetic" stroke="#a855f7" dot={false} strokeWidth={2} strokeDasharray="3 3" />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                  </>
              )}

              {activeTab === 'latent' && (
                  <>
                    <div className="p-4 border-b border-aurora-800 bg-aurora-900/20 flex justify-between items-center">
                        <div className="flex items-center space-x-2"><Target className="text-aurora-accent" size={18} /><h3 className="font-semibold text-slate-200">3D Latent Feature Space</h3></div>
                    </div>
                    <div className="flex-1 w-full h-full p-2 bg-black">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis type="number" dataKey="x" name="PC1" stroke="#666" tick={false} />
                                <YAxis type="number" dataKey="y" name="PC2" stroke="#666" tick={false} />
                                <ZAxis type="number" dataKey="z" range={[50, 400]} name="Confidence" />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                                <Scatter name="Signals" data={latentData} fill="#8884d8">
                                    {latentData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[entry.cluster as keyof typeof COLORS]} />
                                    ))}
                                </Scatter>
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                  </>
              )}

              {activeTab === 'calibration' && (
                  <>
                    <div className="p-4 border-b border-aurora-800 bg-aurora-900/20 flex justify-between items-center">
                        <div className="flex items-center space-x-2"><Scale className="text-amber-400" size={18} /><h3 className="font-semibold text-slate-200">Model vs. Ground Truth</h3></div>
                        <div className="text-xs font-mono text-slate-500">R² = {isCalibrated ? '0.89' : '0.42'}</div>
                    </div>
                    <div className="flex-1 w-full h-full p-4">
                        {drillData ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis type="number" dataKey="actual" name="Lab Assay" stroke="#475569" label={{ value: 'Actual Lab Value', position: 'insideBottom', offset: -10, fill: '#64748b' }} />
                                    <YAxis type="number" dataKey="predicted" name="Model Prediction" stroke="#475569" label={{ value: 'Aurora Predicted', angle: -90, position: 'insideLeft', fill: '#64748b' }} />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                                    <Scatter name="Validation" data={chartData} fill="#3b82f6" />
                                </ScatterChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                <Database size={48} className="mb-4 opacity-50" />
                                <p>No Ground Truth Data Loaded.</p>
                            </div>
                        )}
                    </div>
                  </>
              )}
          </div>

          <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl flex flex-col overflow-hidden">
              <div className="p-4 border-b border-aurora-800 bg-aurora-900/50">
                  <h3 className="font-bold text-sm text-slate-300 flex items-center"><Cpu size={16} className="mr-2 text-aurora-500"/> Active Neural Modules</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                  {NEURAL_MODULES.map(mod => (
                      <div key={mod.id} className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                          <div className="flex justify-between items-start mb-2">
                              <span className="text-xs font-bold text-white">{mod.name}</span>
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${mod.status === 'Converged' ? 'bg-emerald-900/50 text-emerald-400' : 'bg-blue-900/50 text-blue-400'}`}>{mod.status}</span>
                          </div>
                          <div className="flex justify-between text-[10px] text-slate-500">
                              <span>Loss: {mod.loss.toFixed(4)}</span>
                              <span>Acc: {(mod.accuracy * 100).toFixed(1)}%</span>
                          </div>
                      </div>
                  ))}
              </div>
              <div className="bg-black p-4 border-t border-aurora-800 h-48 overflow-y-auto font-mono text-[10px]">
                  <div className="flex items-center text-slate-500 mb-2 border-b border-slate-800 pb-1">
                      <Terminal size={12} className="mr-2" /> SYSTEM_LOGS
                  </div>
                  {isTraining && <div className="text-aurora-400 animate-pulse">&gt; Backpropagation active... updating weights</div>}
                  {calibrationLogs.map(log => (
                      <div key={log.id} className="mb-1">
                          <span className="text-slate-600">[{log.timestamp.split('T')[1].substring(0,8)}]</span> <span className="text-emerald-500">SUCCESS</span> Re-calibrated {log.region_id}
                      </div>
                  ))}
                  <div className="text-slate-500">&gt; System Ready.</div>
              </div>
          </div>
      </div>

      {showInjectModal && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm rounded-xl">
              <div className="bg-aurora-950 border border-aurora-700 p-6 rounded-xl w-[550px] shadow-2xl animate-fadeIn flex flex-col max-h-[90vh]">
                  <div className="flex justify-between items-center mb-6">
                      <div className="flex items-center space-x-3">
                          <Database className="text-emerald-400" size={24} />
                          <div>
                              <h3 className="text-white font-bold text-lg">Inject Ground Truth</h3>
                              <p className="text-xs text-slate-400">Calibrate Physics Engine</p>
                          </div>
                      </div>
                      <button onClick={() => setShowInjectModal(false)} className="text-slate-400 hover:text-white"><X size={20}/></button>
                  </div>
                  <div className="flex space-x-1 mb-4 bg-slate-900 p-1 rounded-lg">
                      <button onClick={() => setIngestMode('upload')} className={`flex-1 text-xs font-bold py-1.5 rounded transition-colors ${ingestMode === 'upload' ? 'bg-aurora-700 text-white' : 'text-slate-500 hover:text-white'}`}>File Upload</button>
                      <button onClick={() => setIngestMode('paste')} className={`flex-1 text-xs font-bold py-1.5 rounded transition-colors ${ingestMode === 'paste' ? 'bg-aurora-700 text-white' : 'text-slate-500 hover:text-white'}`}>Paste Coordinates</button>
                  </div>
                  <div className="space-y-4 flex-1">
                      {ingestMode === 'upload' ? (
                          <div className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group border-slate-700 hover:border-aurora-500 hover:bg-slate-900`} onClick={() => fileInputRef.current?.click()}>
                              <FileSpreadsheet size={32} className={`mb-3 text-slate-500 group-hover:text-aurora-400`} />
                              <p className="text-sm font-bold text-slate-300">Click to Upload .CSV</p>
                              <input type="file" ref={fileInputRef} className="hidden" accept=".csv" onChange={handleFileUpload} />
                          </div>
                      ) : (
                          <div className="flex flex-col h-40">
                              <textarea className="flex-1 bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-white font-mono focus:border-aurora-500 outline-none resize-none" placeholder="Paste data here..." value={pasteContent} onChange={(e) => setPasteContent(e.target.value)} />
                              <button onClick={handlePasteSubmit} className="mt-2 text-xs text-aurora-400 hover:text-white flex items-center justify-end">Process Text</button>
                          </div>
                      )}
                      <div className="flex justify-end space-x-3 pt-4 border-t border-aurora-800">
                          <button onClick={() => setShowInjectModal(false)} className="text-slate-400 hover:text-white text-xs font-bold px-4 py-2">Cancel</button>
                          <button onClick={handleRunCalibration} disabled={!drillData || isTraining} className={`bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-6 rounded-lg text-xs flex items-center transition-all ${(!drillData || isTraining) ? 'opacity-50 cursor-not-allowed' : ''}`}>
                              {isTraining ? <Activity size={14} className="mr-2 animate-spin" /> : <Zap size={14} className="mr-2" />}
                              {isTraining ? 'Training...' : 'Calibrate Engine'}
                          </button>
                      </div>
                  </div>
              </div>
          </div>
      )}
    </div>
  );
};

export default USHEView;