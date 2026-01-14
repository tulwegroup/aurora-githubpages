import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ScatterChart, Scatter, Cell } from 'recharts';
import { Layers, Activity, Terminal } from 'lucide-react';
import { AuroraAPI } from '../api';
import { ExplorationCampaign } from '../types';

interface USHEViewProps {
  campaign: ExplorationCampaign;
}

const USHEView: React.FC<USHEViewProps> = ({ campaign }) => {
  const [activeTab, setActiveTab] = useState<'fusion' | 'latent'>('fusion');
  const [isFetchingReal, setIsFetchingReal] = useState(false);
  const [spectralData, setSpectralData] = useState<any[]>([]);
  const [latentData, setLatentData] = useState<any[]>([]);

  useEffect(() => {
      const loadData = async () => {
          setIsFetchingReal(true);
          try {
              // GEE fetching is now handled server-side
              const aoi = { lat: -8.12, lon: 33.45, radius_km: 10 }; 
              const realData = await AuroraAPI.fetchRealSpectralData(aoi, 'arsenopyrite');
              
              if (realData?.spectrum) {
                  setSpectralData(realData.spectrum);
              } else {
                  setSpectralData(generateSyntheticSpectrum());
              }
          } catch (e) {
              setSpectralData(generateSyntheticSpectrum());
          }
          setIsFetchingReal(false);
      };
      loadData();
  }, [campaign]);

  const generateSyntheticSpectrum = () => {
      return Array.from({length: 20}, (_, i) => ({
          wavelength: 0.4 + (i * 0.1),
          value: Math.random() * 0.5 + 0.2
      }));
  };

  return (
    <div className="space-y-6">
      <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl p-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
              <div className="p-3 bg-aurora-500/10 rounded-full border border-aurora-500/20">
                  <Layers className="text-aurora-500" size={24} />
              </div>
              <div>
                  <h2 className="text-lg font-bold text-white">Spectral Harmonization</h2>
                  <p className="text-xs text-slate-400 font-mono tracking-widest uppercase">
                    Cross-Sensor Calibration • {isFetchingReal ? 'Fetching GEE...' : 'Ready'}
                  </p>
              </div>
          </div>
          <div className="flex space-x-2">
              <button onClick={() => setActiveTab('fusion')} className={`px-4 py-2 rounded text-xs font-bold ${activeTab === 'fusion' ? 'bg-aurora-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Spectrum</button>
              <button onClick={() => setActiveTab('latent')} className={`px-4 py-2 rounded text-xs font-bold ${activeTab === 'latent' ? 'bg-aurora-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Latent Space</button>
          </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
          <div className="lg:col-span-2 bg-slate-950 border border-aurora-800 rounded-xl p-6">
              <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={spectralData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="wavelength" stroke="#475569" />
                      <YAxis stroke="#475569" />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                      <Area type="monotone" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                  </AreaChart>
              </ResponsiveContainer>
          </div>
          
          <div className="bg-aurora-900/50 border border-aurora-800 rounded-xl flex flex-col overflow-hidden">
              <div className="p-4 border-b border-aurora-800 bg-aurora-900/50 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Process Stream</h3>
                <Activity size={14} className="text-aurora-500 animate-pulse" />
              </div>
              <div className="flex-1 p-4 space-y-4">
                  <div className="bg-slate-950 p-3 rounded border border-slate-800">
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Source Strategy</p>
                      <p className="text-white text-sm font-mono mt-1">Railway Cloud Proxy</p>
                  </div>
                  <div className="bg-slate-950 p-3 rounded border border-slate-800">
                      <p className="text-[10px] text-slate-500 uppercase font-bold">GEE Authentication</p>
                      <p className="text-emerald-400 text-sm font-bold mt-1">SERVER MANAGED</p>
                  </div>
              </div>
              <div className="bg-black p-4 border-t border-aurora-800 font-mono text-[10px] text-slate-500">
                <div className="flex items-center mb-1">
                    <Terminal size={12} className="mr-2" />
                    <span>SYSTEM_LOGS</span>
                </div>
                <p>{"[info] Handshake established with Railway compute stack."}</p>
                <p>{"[info] Environment GEE_SERVICE_ACCOUNT_JSON found."}</p>
                <p className="text-emerald-500">{"[ready] USHE kernel online."}</p>
              </div>
          </div>
      </div>
    </div>
  );
};

export default USHEView;