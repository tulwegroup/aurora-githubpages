import React from 'react';
import { AppView } from '../types';
import { ChevronRight, Radio, Globe, Briefcase, Radar, Waves, Layers, Brain, Clock, Settings, Zap } from 'lucide-react';

export interface SidebarProps {
  currentView?: string;
  onNavigate?: (view: string) => void;
  activeTab?: AppView;
  setActiveTab?: React.Dispatch<React.SetStateAction<AppView>>;
  customLogo?: string;
  onSwitchCampaign?: (campaignId: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  currentView, 
  onNavigate,
  activeTab,
  setActiveTab,
  customLogo,
  onSwitchCampaign
}) => {
  const menuItems = [
    { id: 'mission', label: 'Mission Control', icon: Zap, color: 'text-emerald-400' },
    { id: 'dashboard', label: 'Dashboard', icon: Radio, color: 'text-aurora-400' },
    { id: 'map', label: 'Planetary Map', icon: Globe },
    { id: 'portfolio', label: 'Portfolio Command', icon: Briefcase },
    { id: 'osil', label: 'Sensor Integration (OSIL)', icon: Radar },
    { id: 'seismic', label: 'Aurora Seismic (ASS)', icon: Waves },
    { id: 'ushe', label: 'Harmonization (USHE)', icon: Layers },
    { id: 'pcfc', label: 'Physics-Causal Core', icon: Brain },
    { id: 'tmal', label: 'Temporal Analytics', icon: Clock },
    { id: 'qse', label: 'Quantum Engine (QSE)', icon: Brain },
    { id: 'twin', label: 'Digital Twin', icon: Layers },
    { id: 'ietl', label: 'Data Ingestion (IETL)', icon: Radar },
    { id: 'data', label: 'Data Lake', icon: Layers },
    { id: 'config', label: 'System Config', icon: Settings },
  ];

  return (
    <aside className="w-56 bg-aurora-950 border-r border-aurora-800 p-3 h-screen overflow-y-auto flex flex-col">
      {/* Logo */}
      <div className="mb-6">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 bg-gradient-to-br from-aurora-500 to-aurora-700 rounded flex items-center justify-center text-white font-bold text-xs">
            A
          </div>
          <div>
            <h2 className="text-xs font-bold text-white">AURORA</h2>
            <p className="text-[10px] text-aurora-400">v3.0</p>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="space-y-1 flex-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab?.(item.id as AppView)}
              className={`w-full text-left px-3 py-2 rounded transition-all flex items-center space-x-2 text-xs ${
                isActive
                  ? 'bg-aurora-600/30 border border-aurora-500 text-aurora-300'
                  : 'text-slate-400 hover:bg-aurora-900/40 border border-transparent hover:border-aurora-800'
              }`}
            >
              <Icon size={14} className={isActive ? 'text-emerald-400' : 'text-slate-500'} />
              <span className="font-medium truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-aurora-800 pt-3 mt-3 text-[10px] text-slate-500 text-center space-y-1">
        <p className="uppercase tracking-widest">Online</p>
        <p className="text-aurora-600 font-mono">v3.0</p>
      </div>
    </aside>
  );
};

export default Sidebar;
