import React from 'react';
import { AppView } from '../types';

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
  return (
    <aside className="w-64 bg-aurora-950 border-r border-aurora-800 p-4 h-screen overflow-y-auto">
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white">Aurora OSI</h2>
        <nav className="space-y-2">
          <button
            onClick={() => onNavigate('Dashboard')}
            className={`w-full text-left px-4 py-2 rounded transition-colors ${
              currentView === 'Dashboard'
                ? 'bg-aurora-600 text-white'
                : 'text-slate-400 hover:bg-aurora-900'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => onNavigate('Config')}
            className={`w-full text-left px-4 py-2 rounded transition-colors ${
              currentView === 'Config'
                ? 'bg-aurora-600 text-white'
                : 'text-slate-400 hover:bg-aurora-900'
            }`}
          >
            Configuration
          </button>
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
