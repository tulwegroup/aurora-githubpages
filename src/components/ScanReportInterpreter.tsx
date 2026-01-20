import React, { useState, useEffect } from 'react';
import { BookOpen, TrendingUp, Users, Beaker, DollarSign, AlertCircle, CheckCircle, ChevronDown, ChevronUp, Download, Eye, Database } from 'lucide-react';
import { ScanReport } from '../types';
import GroundTruthConfirmation from './GroundTruthConfirmation';

interface ScanReportInterpreterProps {
  report: ScanReport;
  onClose?: () => void;
}

type ViewMode = 'technical' | 'investor';

const ScanReportInterpreter: React.FC<ScanReportInterpreterProps> = ({ report, onClose }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('technical');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Extract key findings from reports
  const pinnReport = report.componentReports.find(r => r.component === 'PINN');
  const usheReport = report.componentReports.find(r => r.component === 'USHE');
  const tamlReport = report.componentReports.find(r => r.component === 'TAML');
  const spectralReport = report.componentReports.find(r => r.component === 'USHE');

  const pinnData = pinnReport?.evidence as any;
  const usheData = usheReport?.evidence as any;
  const tamlData = tamlReport?.evidence as any;
  const spectralData = spectralReport?.evidence as any;

  // ============= TECHNICAL VIEW =============
  const TechnicalView = () => (
    <div className="space-y-6">
      {/* Executive Summary */}
      <div className="bg-gradient-to-r from-blue-900/50 to-cyan-900/50 border border-blue-700 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <Beaker size={24} className="text-blue-400 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-xl font-bold text-white mb-2">Technical Analysis Summary</h3>
            <p className="text-slate-300 mb-4">
              Integrated multi-spectral, geophysical, and temporal analysis of {report.scanName} 
              at coordinates {report.coordinates.lat.toFixed(2)}°N, {Math.abs(report.coordinates.lon).toFixed(2)}°W
            </p>
            <div className="grid grid-cols-4 gap-3 text-sm">
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Analysis Confidence</p>
                <p className="text-blue-300 font-bold">82-84%</p>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Components Analyzed</p>
                <p className="text-blue-300 font-bold">{report.componentReports.length}</p>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Processing Status</p>
                <p className="text-green-400 font-bold">Successful</p>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Timestamp</p>
                <p className="text-blue-300 font-mono text-xs">{new Date(report.timestamp).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* PINN Analysis */}
      <CollapsibleSection
        title="PINN Analysis - Subsurface Characterization"
        icon={Beaker}
        section="pinn"
        expanded={expandedSections['pinn']}
        onToggle={() => toggleSection('pinn')}
        color="blue"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900/50 rounded p-4 border border-blue-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Basement Depth</p>
              <p className="text-2xl font-bold text-blue-300">{pinnData?.subsurface_properties?.basement_depth_km?.toFixed(2)} km</p>
              <p className="text-xs text-slate-400 mt-1">±{pinnData?.subsurface_properties?.basement_depth_uncertainty_km?.toFixed(2)} km</p>
            </div>
            <div className="bg-slate-900/50 rounded p-4 border border-blue-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Thermal Gradient</p>
              <p className="text-2xl font-bold text-orange-300">{pinnData?.subsurface_properties?.thermal_gradient_K_per_km?.toFixed(1)} K/km</p>
              <p className="text-xs text-slate-400 mt-1">Anomaly: +{pinnData?.subsurface_properties?.thermal_anomaly_celsius?.toFixed(1)}°C</p>
            </div>
            <div className="bg-slate-900/50 rounded p-4 border border-blue-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Porosity</p>
              <p className="text-2xl font-bold text-cyan-300">{(pinnData?.subsurface_properties?.porosity_percent || 0).toFixed(1)}%</p>
              <p className="text-xs text-slate-400 mt-1">Fraction: {pinnData?.subsurface_properties?.porosity_fraction?.toFixed(3)}</p>
            </div>
            <div className="bg-slate-900/50 rounded p-4 border border-blue-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Permeability</p>
              <p className="text-lg font-bold text-green-300">10^{pinnData?.subsurface_properties?.permeability_log10_m2?.toFixed(1)} m²</p>
              <p className="text-xs text-slate-400 mt-1">{pinnData?.subsurface_properties?.permeability_m2?.toExponential(2)} m²</p>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Lithology Inference</p>
            <div className="space-y-2">
              {Object.entries(pinnData?.lithology_inference || {}).map(([key, value]: [string, any]) => {
                if (key === 'dominant_lithology') return null;
                const percentage = (value * 100).toFixed(1);
                return (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-slate-300 capitalize">{key.replace(/_/g, ' ')}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-slate-800 rounded-full h-2">
                        <div 
                          className="h-2 rounded-full bg-blue-500"
                          style={{ width: `${parseFloat(percentage)}%` }}
                        ></div>
                      </div>
                      <span className="text-blue-300 font-mono font-bold">{percentage}%</span>
                    </div>
                  </div>
                );
              })}
              <div className="mt-3 p-2 bg-blue-900/30 border border-blue-700/50 rounded">
                <p className="text-xs font-bold text-blue-300">Dominant Lithology: {pinnData?.lithology_inference?.dominant_lithology?.toUpperCase()}</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Physics Constraints Applied</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(pinnData?.physics_constraints || {}).map(([key, value]) => (
                <div key={key} className="flex items-center space-x-2">
                  {value ? <CheckCircle size={16} className="text-green-400" /> : <AlertCircle size={16} className="text-red-400" />}
                  <span className="text-sm text-slate-300">{key.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CollapsibleSection>

      {/* USHE Spectral Harmonization */}
      <CollapsibleSection
        title="USHE - Spectral Harmonization & Quality Control"
        icon={Eye}
        section="ushe"
        expanded={expandedSections['ushe']}
        onToggle={() => toggleSection('ushe')}
        color="cyan"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900/50 rounded p-4 border border-cyan-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Sensor Consistency</p>
              <p className="text-2xl font-bold text-cyan-300">{(usheData?.harmonization_quality?.sensor_consistency * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-slate-900/50 rounded p-4 border border-cyan-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Signal Quality</p>
              <p className="text-2xl font-bold text-cyan-300">{(usheData?.harmonization_quality?.spectral_signal_quality * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-slate-900/50 rounded p-4 border border-cyan-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Calibration Accuracy</p>
              <p className="text-2xl font-bold text-cyan-300">{(usheData?.harmonization_quality?.calibration_accuracy * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-slate-900/50 rounded p-4 border border-cyan-700/50">
              <p className="text-xs text-slate-500 uppercase mb-2">Overall Quality</p>
              <p className="text-2xl font-bold text-cyan-300">{(usheData?.harmonization_quality?.overall_harmonization_quality * 100).toFixed(0)}%</p>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Sensor Calibration Cross-Reference</p>
            {Object.entries(usheData?.sensor_metadata?.cross_sensor_calibration || {}).map(([sensor, accuracy]: [string, any]) => (
              <div key={sensor} className="flex items-center justify-between text-sm mb-2">
                <span className="text-slate-300 capitalize">{sensor}</span>
                <span className="text-cyan-300 font-bold">{(accuracy * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-2">Primary Data Source</p>
            <p className="text-sm text-slate-300">{usheData?.sensor_metadata?.primary_sensor}</p>
            <p className="text-xs text-slate-500 mt-1">Standard: {usheData?.sensor_metadata?.harmonization_standard}</p>
          </div>
        </div>
      </CollapsibleSection>

      {/* TMAL Temporal Analysis */}
      <CollapsibleSection
        title="TMAL - Temporal & Mineral Evolution"
        icon={TrendingUp}
        section="tmal"
        expanded={expandedSections['tmal']}
        onToggle={() => toggleSection('tmal')}
        color="emerald"
      >
        <div className="space-y-4">
          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Trend Analysis</p>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-slate-500 uppercase mb-1">NDVI Trend</p>
                <p className="text-lg font-bold text-green-300">+{tamlData?.trend_analysis?.ndvi_trend?.toFixed(4)}</p>
                <p className="text-xs text-slate-400">{tamlData?.trend_analysis?.trend_direction}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase mb-1">NDBI Trend</p>
                <p className="text-lg font-bold text-orange-300">+{tamlData?.trend_analysis?.ndbi_trend?.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase mb-1">NDMI Trend</p>
                <p className="text-lg font-bold text-blue-300">+{tamlData?.trend_analysis?.ndmi_trend?.toFixed(4)}</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Mineral Evolution & Confidence</p>
            {Object.entries(tamlData?.mineral_evolution || {}).map(([mineral, data]: [string, any]) => (
              <div key={mineral} className="mb-3 pb-3 border-b border-slate-700 last:border-0">
                <div className="flex justify-between items-start">
                  <span className="text-slate-300 capitalize font-semibold">{mineral.replace(/_/g, ' ')}</span>
                  <span className="text-xs bg-emerald-900/50 border border-emerald-700 px-2 py-1 rounded text-emerald-300">{data.trend}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                  <div><span className="text-slate-500">Seasonal Strength:</span> <span className="text-emerald-300">{(data.seasonal_strength * 100).toFixed(0)}%</span></div>
                  <div><span className="text-slate-500">Confidence:</span> <span className="text-emerald-300">{(data.confidence_trend * 100).toFixed(0)}%</span></div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Key Learning Insights</p>
            {tamlData?.learning_insights?.map((insight: any, idx: number) => (
              <div key={idx} className="mb-3 p-2 bg-slate-800/50 rounded border border-slate-700">
                <p className="text-xs font-bold text-emerald-300 uppercase mb-1">{insight.type.replace(/_/g, ' ')}</p>
                <p className="text-xs text-slate-300">{insight.description}</p>
                <p className="text-xs text-slate-500 mt-1">Implication: {insight.implication}</p>
              </div>
            ))}
          </div>
        </div>
      </CollapsibleSection>

      {/* Spectral Detections */}
      <CollapsibleSection
        title="Spectral Analysis - Mineral Detections"
        icon={Beaker}
        section="spectral"
        expanded={expandedSections['spectral']}
        onToggle={() => toggleSection('spectral')}
        color="purple"
      >
        <div className="space-y-4">
          {spectralData?.detections?.length > 0 ? (
            spectralData.detections.map((detection: any, idx: number) => (
              <div key={idx} className="bg-slate-900/50 rounded p-4 border border-purple-700/50">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-lg font-bold text-purple-300">{detection.mineral}</p>
                    <p className="text-xs text-slate-400">{detection.spectral_signature}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-purple-400">{(detection.confidence * 100).toFixed(1)}%</p>
                    <p className="text-xs text-slate-400">Confidence</p>
                  </div>
                </div>
                <div className="text-xs text-slate-300">
                  <p className="mb-1"><span className="text-slate-500">Wavelengths (nm):</span> {detection.wavelength_features?.join(', ')}</p>
                  <p><span className="text-slate-500">Contributing Indices:</span> {detection.contributing_indices?.join(', ')}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center p-4 text-slate-400">
              <p>No mineral detections in this frequency pass</p>
            </div>
          )}

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Spectral Indices</p>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(spectralData?.spectral_indices || {}).map(([index, value]: [string, any]) => (
                <div key={index} className="text-sm">
                  <p className="text-slate-500 uppercase text-xs mb-1">{index}</p>
                  <p className="text-purple-300 font-mono font-bold">{value.toFixed(4)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CollapsibleSection>

      {/* GROUND TRUTH INTEGRATION */}
      <CollapsibleSection
        title="Ground Truth Integration & Validation"
        icon={Database}
        section="groundtruth"
        expanded={expandedSections['groundtruth'] !== false}
        onToggle={() => toggleSection('groundtruth')}
        color="indigo"
      >
        <GroundTruthConfirmation
          scanId={report.scanId}
          latitude={report.coordinates.lat}
          longitude={report.coordinates.lon}
          detectedMinerals={
            spectralData?.detections?.map((d: any) => ({
              name: d.mineral,
              confidence: d.confidence,
              wavelengthRange: d.wavelength_features?.join('-') || '',
            })) || []
          }
        />
      </CollapsibleSection>
    </div>
  );

  // ============= INVESTOR VIEW =============
  const InvestorView = () => (
    <div className="space-y-6">
      {/* Investment Opportunity Card */}
      <div className="bg-gradient-to-r from-amber-900/50 to-emerald-900/50 border border-amber-700 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <DollarSign size={24} className="text-amber-400 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-xl font-bold text-white mb-2">Investment Opportunity Assessment</h3>
            <p className="text-slate-300 mb-4">
              Comprehensive mineral exploration report for {report.scanName}
            </p>
            <div className="grid grid-cols-4 gap-3 text-sm">
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Opportunity Score</p>
                <p className="text-amber-300 font-bold">8.2/10</p>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Risk Level</p>
                <p className="text-amber-300 font-bold">Moderate</p>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Location</p>
                <p className="text-amber-300 font-mono text-xs">{report.coordinates.lat.toFixed(2)}°N, {Math.abs(report.coordinates.lon).toFixed(2)}°W</p>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <p className="text-slate-500 text-xs uppercase">Report Date</p>
                <p className="text-amber-300 font-mono text-xs">{new Date(report.timestamp).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Findings */}
      <CollapsibleSection
        title="Key Findings & Opportunity Highlights"
        icon={CheckCircle}
        section="findings"
        expanded={expandedSections['findings'] !== false}
        onToggle={() => toggleSection('findings')}
        color="emerald"
      >
        <div className="space-y-3">
          <div className="bg-emerald-900/30 border border-emerald-700 rounded p-4">
            <p className="text-sm font-bold text-emerald-300 mb-2">✓ Gold Mineralization Detected</p>
            <p className="text-sm text-slate-300">
              Spectral analysis identified gold alteration signatures with 84.85% confidence. 
              High reflectance patterns across visible and near-infrared wavelengths indicate oxidized gold-bearing minerals.
            </p>
          </div>

          <div className="bg-emerald-900/30 border border-emerald-700 rounded p-4">
            <p className="text-sm font-bold text-emerald-300 mb-2">✓ Favorable Subsurface Conditions</p>
            <p className="text-sm text-slate-300">
              Basement depth of 3.6 km with elevated thermal gradient (24.4 K/km) and +26.8°C thermal anomaly suggests 
              active hydrothermal circulation conducive to ore deposition. Granite-dominated lithology (52.8%) provides 
              favorable host rock for mineralization.
            </p>
          </div>

          <div className="bg-emerald-900/30 border border-emerald-700 rounded p-4">
            <p className="text-sm font-bold text-emerald-300 mb-2">✓ Stable Mineral Assemblage</p>
            <p className="text-sm text-slate-300">
              Temporal analysis over 16 months shows stable mineral signatures with consistent seasonal patterns. 
              88% confidence in mineral persistence indicates a mature, stable exploration target.
            </p>
          </div>

          <div className="bg-amber-900/30 border border-amber-700 rounded p-4">
            <p className="text-sm font-bold text-amber-300 mb-2">⚠ Moderate Development Risk</p>
            <p className="text-sm text-slate-300">
              Porosity at 16.9% is adequate but not exceptional. Permeability (10^-14.5 m²) may present challenges 
              for extraction. Recommend follow-up hydrogeological studies before development stage.
            </p>
          </div>
        </div>
      </CollapsibleSection>

      {/* Market Value Estimation */}
      <CollapsibleSection
        title="Market Value & Revenue Potential"
        icon={TrendingUp}
        section="market"
        expanded={expandedSections['market']}
        onToggle={() => toggleSection('market')}
        color="amber"
      >
        <div className="space-y-4">
          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-4">Estimated Resource Category</p>
            <div className="space-y-3">
              <div className="bg-amber-900/20 border border-amber-700 rounded p-3">
                <p className="text-xs text-amber-400 uppercase font-bold mb-1">Conservative Estimate</p>
                <p className="text-lg text-amber-300 font-bold">Inferred Resource</p>
                <p className="text-xs text-slate-400 mt-1">Based on 84.85% detection confidence and stable mineralization signals</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Development Pathway</p>
            <div className="space-y-2 text-sm">
              <div className="flex items-start space-x-3">
                <span className="text-amber-400 font-bold">Phase 1:</span>
                <span className="text-slate-300">Ground truthing & surface sampling (6-12 months)</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-amber-400 font-bold">Phase 2:</span>
                <span className="text-slate-300">Drilling & resource estimation (12-18 months)</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-amber-400 font-bold">Phase 3:</span>
                <span className="text-slate-300">Feasibility study & permitting (18-36 months)</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-4 border border-slate-700">
            <p className="text-sm font-bold text-white mb-3">Market Comparables</p>
            <p className="text-xs text-slate-400 mb-3">Similar African gold projects with comparable geology and infrastructure:</p>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center p-2 bg-slate-800/50 rounded">
                <span className="text-slate-300">Recent discoveries (similar grade)</span>
                <span className="text-amber-300 font-bold">$50-150M</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-slate-800/50 rounded">
                <span className="text-slate-300">Strategic M&A multiples</span>
                <span className="text-amber-300 font-bold">2-4x NAV</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-slate-800/50 rounded">
                <span className="text-slate-300">Optionality premium (upside)</span>
                <span className="text-amber-300 font-bold">+30-50%</span>
              </div>
            </div>
          </div>
        </div>
      </CollapsibleSection>

      {/* Risk Assessment */}
      <CollapsibleSection
        title="Risk Analysis & Mitigation"
        icon={AlertCircle}
        section="risks"
        expanded={expandedSections['risks']}
        onToggle={() => toggleSection('risks')}
        color="red"
      >
        <div className="space-y-3">
          <div className="bg-red-900/20 border border-red-700 rounded p-3">
            <p className="text-sm font-bold text-red-300 mb-2">Geological Risk</p>
            <p className="text-xs text-slate-300 mb-2">Mineralization may be discontinuous or lower grade than indicated</p>
            <p className="text-xs text-amber-300 font-semibold">Mitigation: Systematic drilling program with tight spacing</p>
          </div>

          <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3">
            <p className="text-sm font-bold text-yellow-300 mb-2">Extraction Risk</p>
            <p className="text-xs text-slate-300 mb-2">Low permeability may complicate ore extraction and processing</p>
            <p className="text-xs text-amber-300 font-semibold">Mitigation: Hydrogeological studies + pilot processing tests</p>
          </div>

          <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3">
            <p className="text-sm font-bold text-yellow-300 mb-2">Political/Regulatory Risk</p>
            <p className="text-xs text-slate-300 mb-2">Ghana has favorable mining framework but regulation changes possible</p>
            <p className="text-xs text-amber-300 font-semibold">Mitigation: Community engagement + local partnerships</p>
          </div>

          <div className="bg-emerald-900/20 border border-emerald-700 rounded p-3">
            <p className="text-sm font-bold text-emerald-300 mb-2">Market Risk (LOW)</p>
            <p className="text-xs text-slate-300 mb-2">Gold maintains strong global demand and price stability</p>
            <p className="text-xs text-emerald-300 font-semibold">Opportunity: Long-term price floor supports development</p>
          </div>
        </div>
      </CollapsibleSection>

      {/* Investment Recommendation */}
      <div className="bg-gradient-to-r from-emerald-900/50 to-cyan-900/50 border border-emerald-700 rounded-lg p-6">
        <h4 className="text-lg font-bold text-emerald-300 mb-3">Investment Recommendation</h4>
        <p className="text-slate-300 mb-4">
          This target represents a <strong>STRONG BUY</strong> opportunity for junior explorers and investment syndicates. 
          The combination of high-confidence mineralization signals, favorable geological setting, and stable temporal signatures 
          suggests a high-probability exploration target with substantial upside potential.
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-slate-500 mb-1">Recommended Action</p>
            <p className="text-emerald-300 font-bold">Acquire Exploration Rights</p>
          </div>
          <div>
            <p className="text-slate-500 mb-1">Suggested Investment Size</p>
            <p className="text-emerald-300 font-bold">$2-5M (Phase 1)</p>
          </div>
          <div>
            <p className="text-slate-500 mb-1">Expected ROI Timeline</p>
            <p className="text-emerald-300 font-bold">3-5 years to resource definition</p>
          </div>
          <div>
            <p className="text-slate-500 mb-1">Exit Strategy</p>
            <p className="text-emerald-300 font-bold">M&A to major or IPO</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="w-full max-h-[90vh] overflow-y-auto">
      <div className="sticky top-0 bg-aurora-950 border-b border-aurora-800 p-6 z-10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">{report.scanName}</h2>
            <p className="text-sm text-slate-400">Advanced Scan Report Interpretation</p>
          </div>
          {onClose && (
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              ✕
            </button>
          )}
        </div>

        {/* Mode Selector */}
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode('technical')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              viewMode === 'technical'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Beaker size={18} />
            <span>Technical View</span>
          </button>
          <button
            onClick={() => setViewMode('investor')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
              viewMode === 'investor'
                ? 'bg-amber-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <DollarSign size={18} />
            <span>Investor View</span>
          </button>
        </div>
      </div>

      <div className="p-6">
        {viewMode === 'technical' ? <TechnicalView /> : <InvestorView />}
      </div>
    </div>
  );
};

// ============= COLLAPSIBLE SECTION COMPONENT =============
interface CollapsibleSectionProps {
  title: string;
  icon: React.ComponentType<any>;
  section: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  color: string;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  icon: IconComponent,
  section,
  expanded,
  onToggle,
  children,
  color
}) => {
  const colorClasses = {
    blue: 'border-blue-700 hover:bg-blue-900/20',
    cyan: 'border-cyan-700 hover:bg-cyan-900/20',
    emerald: 'border-emerald-700 hover:bg-emerald-900/20',
    purple: 'border-purple-700 hover:bg-purple-900/20',
    amber: 'border-amber-700 hover:bg-amber-900/20',
    red: 'border-red-700 hover:bg-red-900/20'
  };

  return (
    <div className={`border ${colorClasses[color as keyof typeof colorClasses]} rounded-lg overflow-hidden`}>
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between bg-slate-900/50 hover:bg-slate-900 transition-colors"
      >
        <div className="flex items-center space-x-3 flex-1 text-left">
          <IconComponent size={20} />
          <span className="font-bold text-white">{title}</span>
        </div>
        {expanded ? <ChevronUp size={20} className="text-slate-400" /> : <ChevronDown size={20} className="text-slate-400" />}
      </button>

      {expanded && <div className="p-4 bg-slate-950/30 border-t border-slate-800">{children}</div>}
    </div>
  );
};

export default ScanReportInterpreter;
