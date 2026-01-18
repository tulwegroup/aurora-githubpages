import React from 'react';
import { AppView } from '../types';
import { ChevronRight, Radio, Globe, Briefcase, Radar, Waves, Layers, Brain, Clock, Settings } from 'lucide-react';

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
    { id: 'dashboard', label: 'Mission Control', icon: Radio, color: 'text-emerald-400' },
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
    <aside className="w-64 bg-aurora-950 border-r border-aurora-800 p-4 h-screen overflow-y-auto flex flex-col">
      {/* Logo */}
      <div className="mb-8">
        <div className="flex items-center space-x-2 mb-2">
          <div className="w-8 h-8 bg-gradient-to-br from-aurora-500 to-aurora-700 rounded flex items-center justify-center text-white font-bold text-sm">
            A
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">AURORA</h2>
            <p className="text-xs text-aurora-400">OSI v3.0</p>
          </div>
        </div>
      </div>

      {/* Active Mission */}
      <div className="mb-6 p-4 bg-aurora-900/40 border border-aurora-800 rounded-lg">
        <p className="text-xs text-slate-400 font-mono uppercase mb-2">ACTIVE MISSION</p>
        <div className="flex items-start justify-between group cursor-pointer hover:bg-aurora-800/30 p-2 rounded transition-colors">
          <p className="text-sm font-bold text-white truncate">Tanzania / Mozambique Belt</p>
          <ChevronRight size={16} className="text-aurora-500 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="space-y-2 flex-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab?.(item.id as AppView)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all flex items-center space-x-3 ${
                isActive
                  ? 'bg-aurora-600/30 border border-aurora-500 text-aurora-300 shadow-lg'
                  : 'text-slate-400 hover:bg-aurora-900/40 border border-transparent hover:border-aurora-800'
              }`}
            >
              <Icon size={16} className={isActive ? 'text-emerald-400' : 'text-slate-500'} />
              <span className="text-sm font-medium">{item.label}</span>
              {isActive && <Radio size={12} className="ml-auto text-emerald-400 animate-pulse" />}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-aurora-800 pt-4 mt-4 text-xs text-slate-500 text-center">
        <p>SYSTEM OPERATIONAL</p>
        <p className="text-aurora-600 font-mono">v3.0.0</p>
      </div>
    </aside>
  );
};

export default Sidebar;
