import React, { Component, useState, useEffect, Suspense, lazy, ErrorInfo, ReactNode } from 'react';
import Sidebar from './components/Sidebar';
import { Bell, Search, User, ShieldCheck, Server, AlertTriangle, RefreshCw, Loader2 } from 'lucide-react';
import { ExplorationCampaign, CAMPAIGN_PHASES, AppView, HiveMindState, MineralAgentType } from './types';
import { ACTIVE_CAMPAIGN } from './constants';
import { AuroraAPI } from './api';
import { APP_CONFIG } from './config';

// --- LAZY LOAD SUB-SYSTEMS ---
const Dashboard = lazy(() => import('./components/Dashboard'));
const ConfigView = lazy(() => import('./components/ConfigView'));
const USHEView = lazy(() => import('./components/USHEView'));
const ScanStatusMonitor = lazy(() => import('./components/ScanStatusMonitor'));
const OSILView = lazy(() => import('./components/OSILView'));
const PCFCView = lazy(() => import('./components/PCFCView'));
const QSEView = lazy(() => import('./components/QSEView'));
const IETLView = lazy(() => import('./components/IETLView'));
const TMALView = lazy(() => import('./components/TMALView'));
const DataLakeView = lazy(() => import('./components/DataLakeView'));
const DigitalTwinView = lazy(() => import('./components/DigitalTwinView'));
const PortfolioView = lazy(() => import('./components/PortfolioView'));
const SeismicView = lazy(() => import('./components/SeismicView'));
const PlanetaryMapView = lazy(() => import('./components/PlanetaryMapView')); 

interface ErrorBoundaryProps { children?: ReactNode; }
interface ErrorBoundaryState { hasError: boolean; error: Error | null; }

// Fix: Correct inheritance by explicitly using React.Component to resolve visibility errors in src/App.tsx
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  // Fix: Explicitly declare state property
  state: ErrorBoundaryState = { hasError: false, error: null };

  constructor(props: ErrorBoundaryProps) {
    super(props);
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState { return { hasError: true, error }; }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) { console.error("Critical Failure:", error, errorInfo); }
  
  // Fix: Explicitly cast this to any to access setState in arrow function property
  handleReload = () => { 
    (this as any).setState({ hasError: false, error: null }); 
    window.location.reload(); 
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 p-8 text-center bg-aurora-950/50 rounded-xl border border-aurora-800 animate-fadeIn">
          <AlertTriangle size={48} className="text-red-500 mb-6" />
          <h2 className="text-2xl font-bold text-white mb-2">Interface Malfunction</h2>
          <button onClick={this.handleReload} className="bg-aurora-600 hover:bg-aurora-500 text-white px-8 py-3 rounded-lg font-bold flex items-center transition-all">
            <RefreshCw size={18} className="mr-2" /> Reboot
          </button>
        </div>
      );
    }
    // Fix: Explicitly cast this to any for props access
    return (this as any).props.children;
  }
}

const ViewLoader = () => (
  <div className="flex flex-col items-center justify-center h-[600px] text-slate-500">
    <Loader2 size={48} className="text-aurora-500 animate-spin mb-4" />
    <p className="font-mono text-sm tracking-widest text-aurora-400 animate-pulse">SYNCHRONIZING MODULES...</p>
  </div>
);

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AppView>('dashboard');
  const [campaign, setCampaign] = useState<ExplorationCampaign>(ACTIVE_CAMPAIGN);
  const [campaigns, setCampaigns] = useState<ExplorationCampaign[]>([ACTIVE_CAMPAIGN]);
  const [customLogo, setCustomLogo] = useState<string | null>(null);
  const [isBooting, setIsBooting] = useState(true);
  const [bootStep, setBootStep] = useState('Initializing Secure Enclave...');
  const [hiveMind, setHiveMind] = useState<HiveMindState>({ isScanning: false, scanGrid: [], activeAgents: ['Au'], logs: [], progress: 0, hits: 0, misses: 0 });

  useEffect(() => {
    const bootSystem = async () => {
       setBootStep('Validating API Gateway...');
       await AuroraAPI.init();
       setBootStep('Connecting to Mission Database...');
       const active = await AuroraAPI.getActiveCampaign();
       setCampaign(active);
       setBootStep('Verifying Subsystem Integrity...');
       await new Promise(r => setTimeout(r, 600)); 
       setIsBooting(false);
    };
    bootSystem();
  }, []);

  useEffect(() => {
    const pollJobStatus = async () => {
      if (campaign.status === 'Active' && campaign.jobId) {
        try {
          const status = await AuroraAPI.getJobStatus(campaign.jobId);
          let updatedCampaign = { ...campaign };
          updatedCampaign.phaseProgress = status.progress;
          if (status.status === 'COMPLETED') {
            const results = await AuroraAPI.getJobResults(campaign.jobId);
            updatedCampaign = { ...updatedCampaign, status: 'Completed', phaseProgress: 100, results: results.results || [], drillTargets: results.drillTargets || [] };
          } else if (status.status === 'FAILED') {
            updatedCampaign = { ...updatedCampaign, status: 'Paused', jobId: undefined };
          }
          setCampaign(updatedCampaign);
        } catch (e) { console.error("Poll Failed", e); }
      }
    };
    const interval = setInterval(pollJobStatus, 5000);
    return () => clearInterval(interval);
  }, [campaign]);

  const handleLaunch = async (c: ExplorationCampaign) => { setCampaign(c); await AuroraAPI.updateCampaign(c); };
  const handleUpdate = async (c: ExplorationCampaign) => { setCampaign(c); await AuroraAPI.updateCampaign(c); };
  const handleSwitch = async (campaignId: string) => {
    const selectedCampaign = campaigns.find((c) => c.id === campaignId);
    if (selectedCampaign) {
      setCampaign(selectedCampaign);
      await AuroraAPI.updateCampaign(selectedCampaign);
      setActiveTab('dashboard');
    }
  };

  const renderContent = () => {
    let ViewComponent: any;
    switch (activeTab) {
      case 'dashboard': ViewComponent = Dashboard; break;
      case 'map': ViewComponent = PlanetaryMapView; break;
      case 'portfolio': ViewComponent = PortfolioView; break;
      case 'osil': ViewComponent = OSILView; break;
      case 'seismic': ViewComponent = SeismicView; break;
      case 'ushe': ViewComponent = USHEView; break;
      case 'pcfc': ViewComponent = PCFCView; break;
      case 'tmal': ViewComponent = TMALView; break;
      case 'qse': ViewComponent = QSEView; break;
      case 'twin': ViewComponent = DigitalTwinView; break;
      case 'ietl': ViewComponent = IETLView; break;
      case 'data': ViewComponent = DataLakeView; break;
      case 'config': ViewComponent = ConfigView; break;
      default: ViewComponent = Dashboard; break;
    }
    return (
      <ErrorBoundary>
        <Suspense fallback={<ViewLoader />}>
          <ViewComponent 
            campaign={campaign} 
            onLaunchCampaign={handleLaunch} 
            onUpdateCampaign={handleUpdate} 
            onNavigate={setActiveTab}
            hiveMindState={hiveMind}
            setHiveMindState={setHiveMind}
            customLogo={customLogo}
            setCustomLogo={setCustomLogo}
          />
        </Suspense>
      </ErrorBoundary>
    );
  };

  if (isBooting) {
     return (
        <div className="min-h-screen bg-aurora-950 flex flex-col items-center justify-center text-slate-200">
           <div className="relative mb-8"><div className="w-24 h-24 rounded-full border-4 border-slate-800 border-t-aurora-500 animate-spin"></div><div className="absolute inset-0 flex items-center justify-center font-bold text-2xl text-white font-mono">A</div></div>
           <h1 className="text-2xl font-bold tracking-widest mb-2 font-mono">AURORA OSI v3</h1><p className="text-aurora-400 font-mono text-sm animate-pulse">{bootStep}</p>
        </div>
     );
  }

  return (
    <div className="flex min-h-screen bg-aurora-950 font-sans text-slate-200 selection:bg-aurora-500/30">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} customLogo={customLogo} onSwitchCampaign={handleSwitch} />
      <main className="ml-64 flex-1 flex flex-col">
        <header className="h-16 border-b border-aurora-800 bg-aurora-950/80 backdrop-blur-md sticky top-0 z-40 px-8 flex items-center justify-between">
          <div className="relative w-96 font-mono text-xs text-slate-500">SYSTEM_OPERATIONAL // SECURE_CLOUD_ACTIVE</div>
          <div className="flex items-center space-x-6">
            <div className="text-right">
                <p className="text-sm font-medium text-white">{campaign.regionName || campaign.targetCoordinates}</p>
                <p className="text-[10px] text-aurora-500 font-bold uppercase tracking-widest">{campaign.status}</p>
            </div>
            <div className="w-9 h-9 bg-slate-800 rounded-full flex items-center justify-center border border-aurora-700 shadow-inner"><User size={16} className="text-slate-400" /></div>
          </div>
        </header>
        <div className="flex-1 p-8 overflow-y-auto custom-scrollbar">{renderContent()}</div>
      </main>
    </div>
  );
};

export default App;