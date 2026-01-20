import React, { useState } from 'react';
import { FileText, MapPin, Clock, Download, Eye, Archive, Filter, ChevronDown, CheckCircle, AlertCircle, Zap, BookOpen } from 'lucide-react';
import { ScanHistory, ScanReport, ComponentReport } from '../types';
import ScanReportInterpreter from './ScanReportInterpreter';

interface ReportsViewProps {
  scanHistory: ScanHistory;
  activeScanLocation?: { lat: number; lon: number; name: string } | null;
  onNavigate?: (view: string) => void;
}

const ReportsView: React.FC<ReportsViewProps> = ({ scanHistory, activeScanLocation, onNavigate }) => {
  const [expandedReportId, setExpandedReportId] = useState<string | null>(null);
  const [filterComponent, setFilterComponent] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'name'>('date');
  const [selectedReportForInterpretation, setSelectedReportForInterpretation] = useState<ScanReport | null>(null);

  const reports = scanHistory.scans || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-400 bg-green-500/10';
      case 'failed': return 'text-red-400 bg-red-500/10';
      case 'pending': return 'text-yellow-400 bg-yellow-500/10';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle size={16} className="text-green-400" />;
      case 'failed': return <AlertCircle size={16} className="text-red-400" />;
      case 'pending': return <Zap size={16} className="text-yellow-400" />;
      default: return <FileText size={16} className="text-slate-400" />;
    }
  };

  const componentColors: Record<string, string> = {
    'PINN': 'bg-purple-500/20 border-purple-500/50 text-purple-300',
    'USHE': 'bg-blue-500/20 border-blue-500/50 text-blue-300',
    'QSE': 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300',
    'TAML': 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300',
    'SEEPAGE': 'bg-orange-500/20 border-orange-500/50 text-orange-300',
    'LATENT': 'bg-pink-500/20 border-pink-500/50 text-pink-300',
    'PCFC': 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300',
    'OSIL': 'bg-red-500/20 border-red-500/50 text-red-300',
    'IETL': 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300',
    'TWIN': 'bg-teal-500/20 border-teal-500/50 text-teal-300',
  };

  const exportReportJSON = (report: ScanReport) => {
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scan_${report.id}_${new Date(report.timestamp).toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportInvestorPackage = (reports: ScanReport[]) => {
    const package_data = {
      generatedAt: new Date().toISOString(),
      formatVersion: '1.0',
      totalScans: reports.length,
      scans: reports,
      summary: {
        totalAnalysisTime: reports.reduce((sum, r) => sum + (r.totalAnalysisTime || 0), 0),
        successfulScans: reports.filter(r => r.componentReports.some(cr => cr.status === 'success')).length,
        componentsAnalyzed: new Set(reports.flatMap(r => r.componentReports.map(cr => cr.component))).size,
      }
    };

    const dataStr = JSON.stringify(package_data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aurora_investor_package_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const filteredReports = reports
    .filter(r => filterComponent === 'all' || r.componentReports.some(cr => cr.component === filterComponent))
    .sort((a, b) => {
      if (sortBy === 'date') return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      return a.scanName.localeCompare(b.scanName);
    });

  const uniqueComponents = Array.from(new Set(reports.flatMap(r => r.componentReports.map(cr => cr.component))));

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-white font-mono">SCAN REPORTS REPOSITORY</h1>
        <p className="text-slate-400">Historical scan data, evidence trails, and investor-ready packages</p>
      </div>

      {/* Active Scan Info */}
      {activeScanLocation && (
        <div className="bg-aurora-900/40 border border-aurora-700 rounded-lg p-6 space-y-3">
          <div className="flex items-center space-x-2">
            <Zap size={20} className="text-aurora-400" />
            <h2 className="text-lg font-bold text-aurora-300">Active Scan</h2>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-slate-500 text-xs uppercase mb-1">Location</p>
              <p className="text-white font-mono">{activeScanLocation.name}</p>
            </div>
            <div>
              <p className="text-slate-500 text-xs uppercase mb-1">Coordinates</p>
              <p className="text-white font-mono">{activeScanLocation.lat.toFixed(2)}°, {activeScanLocation.lon.toFixed(2)}°</p>
            </div>
            <div>
              <p className="text-slate-500 text-xs uppercase mb-1">Total Scans Saved</p>
              <p className="text-aurora-300 font-bold text-lg">{reports.length}</p>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 bg-aurora-950/50 border border-aurora-800 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <Filter size={18} className="text-aurora-400" />
          <label className="text-sm text-slate-400">Filter by Component:</label>
          <select 
            value={filterComponent}
            onChange={(e) => setFilterComponent(e.target.value)}
            className="bg-aurora-900/50 border border-aurora-700 rounded px-3 py-1 text-white text-sm"
          >
            <option value="all">All Components</option>
            {uniqueComponents.map(comp => (
              <option key={comp} value={comp}>{comp}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label className="text-sm text-slate-400">Sort by:</label>
          <select 
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'date' | 'name')}
            className="bg-aurora-900/50 border border-aurora-700 rounded px-3 py-1 text-white text-sm"
          >
            <option value="date">Newest First</option>
            <option value="name">Scan Name</option>
          </select>
        </div>

        <button
          onClick={() => exportInvestorPackage(filteredReports)}
          className="ml-auto bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded flex items-center space-x-2 transition-colors text-sm"
        >
          <Archive size={16} />
          <span>Export Investor Package</span>
        </button>
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        {filteredReports.length === 0 ? (
          <div className="bg-aurora-900/20 border border-aurora-800 rounded-lg p-12 text-center">
            <FileText size={48} className="mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400">No scan reports found. Complete a scan to generate reports.</p>
          </div>
        ) : (
          filteredReports.map((report) => (
            <div 
              key={report.id}
              className="bg-aurora-900/20 border border-aurora-800 rounded-lg overflow-hidden transition-all hover:border-aurora-600"
            >
              {/* Report Header */}
              <button
                onClick={() => setExpandedReportId(expandedReportId === report.id ? null : report.id)}
                className="w-full p-4 flex items-center justify-between hover:bg-aurora-900/30 transition-colors"
              >
                <div className="flex items-center space-x-4 flex-1 text-left">
                  <MapPin size={20} className="text-aurora-400" />
                  <div>
                    <h3 className="text-lg font-bold text-white">{report.scanName}</h3>
                    <div className="flex items-center space-x-4 text-sm text-slate-400 mt-1">
                      <span className="flex items-center space-x-1">
                        <Clock size={14} />
                        <span>{new Date(report.timestamp).toLocaleDateString()} {new Date(report.timestamp).toLocaleTimeString()}</span>
                      </span>
                      <span className="font-mono">({report.coordinates.lat.toFixed(2)}°, {report.coordinates.lon.toFixed(2)}°)</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <p className="text-sm font-bold text-aurora-300">{report.componentReports.length} Components</p>
                    <p className="text-xs text-slate-500">{report.componentReports.filter(c => c.status === 'success').length} Successful</p>
                  </div>
                  <ChevronDown 
                    size={20} 
                    className={`text-slate-500 transition-transform ${expandedReportId === report.id ? 'rotate-180' : ''}`}
                  />
                </div>
              </button>

              {/* Report Details */}
              {expandedReportId === report.id && (
                <div className="border-t border-aurora-800 p-4 space-y-4 bg-aurora-950/30">
                  <p className="text-sm text-slate-300">{report.summary}</p>

                  {/* Component Reports */}
                  <div className="space-y-3">
                    <p className="text-xs font-bold text-slate-500 uppercase">Component Evidence</p>
                    <div className="grid grid-cols-1 gap-2">
                      {report.componentReports.map((compReport, idx) => (
                        <div 
                          key={idx}
                          className={`border rounded p-3 space-y-2 ${componentColors[compReport.component] || 'bg-slate-500/10 border-slate-500/50'}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              {getStatusIcon(compReport.status)}
                              <span className="font-bold text-sm">{compReport.component}</span>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded ${getStatusColor(compReport.status)}`}>
                              {compReport.status.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300">{compReport.summary}</p>
                          {compReport.metrics && (
                            <div className="text-xs space-y-1 pt-2 border-t border-current/20">
                              {Object.entries(compReport.metrics).map(([key, value]) => (
                                <div key={key} className="flex justify-between">
                                  <span className="opacity-70">{key}:</span>
                                  <span className="font-mono">{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-4 border-t border-aurora-800">
                    <button
                      onClick={() => setSelectedReportForInterpretation(report)}
                      className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded flex items-center justify-center space-x-2 transition-colors text-sm"
                    >
                      <BookOpen size={16} />
                      <span>Interpret Report</span>
                    </button>
                    <button
                      onClick={() => exportReportJSON(report)}
                      className="flex-1 bg-aurora-600 hover:bg-aurora-500 text-white px-4 py-2 rounded flex items-center justify-center space-x-2 transition-colors text-sm"
                    >
                      <Download size={16} />
                      <span>Export as JSON</span>
                    </button>
                    <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded flex items-center justify-center space-x-2 transition-colors text-sm">
                      <Eye size={16} />
                      <span>View Details</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Statistics */}
      {filteredReports.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-aurora-900/40 border border-aurora-700 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase mb-2">Total Scans</p>
            <p className="text-2xl font-bold text-aurora-300">{filteredReports.length}</p>
          </div>
          <div className="bg-green-900/40 border border-green-700 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase mb-2">Successful</p>
            <p className="text-2xl font-bold text-green-300">{filteredReports.filter(r => r.componentReports.some(c => c.status === 'success')).length}</p>
          </div>
          <div className="bg-blue-900/40 border border-blue-700 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase mb-2">Components</p>
            <p className="text-2xl font-bold text-blue-300">{new Set(filteredReports.flatMap(r => r.componentReports.map(c => c.component))).size}</p>
          </div>
          <div className="bg-purple-900/40 border border-purple-700 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase mb-2">Total Evidence</p>
            <p className="text-2xl font-bold text-purple-300">{filteredReports.reduce((sum, r) => sum + r.componentReports.length, 0)}</p>
          </div>
        </div>
      )}

      {/* Report Interpreter Modal */}
      {selectedReportForInterpretation && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-aurora-950 rounded-lg shadow-2xl max-w-5xl w-full max-h-[90vh] border border-aurora-800">
            <ScanReportInterpreter 
              report={selectedReportForInterpretation}
              onClose={() => setSelectedReportForInterpretation(null)}
            />
          </div>
        </div>
      )}
};

export default ReportsView;
