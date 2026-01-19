import React, { useState, useEffect, useRef } from 'react';
import { Map, MapPin, Zap, AlertCircle } from 'lucide-react';

interface VisualizationProps {
  scan: {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    status: string;
    results?: {
      pinn?: any;
      ushe?: any;
      tmal?: any;
    };
  };
  vizData2D?: any;
  vizData3D?: any;
}

/**
 * Map-Based 2D Visualization Component
 * Displays scan results on an interactive map with overlays
 */
export const MapVisualization: React.FC<VisualizationProps> = ({ scan, vizData2D }) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [selectedLayer, setSelectedLayer] = useState<'pinn' | 'ushe' | 'tmal'>('pinn');

  useEffect(() => {
    // Initialize map (would use Leaflet, Mapbox, or similar library)
    if (mapRef.current && !mapLoaded) {
      initializeMap();
      setMapLoaded(true);
    }
  }, [mapLoaded]);

  const initializeMap = () => {
    // Placeholder for map initialization
    // In production, would initialize Leaflet/Mapbox with:
    // - Satellite base layer
    // - Scan location marker
    // - Analysis result overlays (heatmaps, polygons, etc.)
    // - Color-coded confidence scores
  };

  return (
    <div className="w-full bg-slate-900 rounded-lg overflow-hidden">
      <div className="bg-slate-800 p-3 border-b border-slate-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Map className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">2D Map Visualization</h3>
          </div>
          <div className="text-xs text-slate-400">
            {scan.latitude.toFixed(4)}°, {scan.longitude.toFixed(4)}°
          </div>
        </div>

        {/* Layer Selection */}
        <div className="flex gap-2">
          {(['pinn', 'ushe', 'tmal'] as const).map((layer) => (
            <button
              key={layer}
              onClick={() => setSelectedLayer(layer)}
              className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
                selectedLayer === layer
                  ? 'bg-cyan-500 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {layer.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Map Container */}
      <div
        ref={mapRef}
        className="w-full h-64 bg-slate-950 relative"
        style={{
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width="100" height="100" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="M0 0h100v100H0z" fill="%231e293b"/%3E%3Ccircle cx="50" cy="50" r="30" fill="%232d3a4f" opacity="0.3"/%3E%3C/svg%3E")',
          backgroundSize: '200px 200px'
        }}
      >
        {/* Map placeholder content */}
        <div className="w-full h-full flex items-center justify-center flex-col gap-3 text-slate-400">
          <MapPin className="w-8 h-8" />
          <div className="text-center">
            <p className="text-sm">Map Region</p>
            <p className="text-xs text-slate-500">
              {scan.name} • {selectedLayer.toUpperCase()} Layer
            </p>
          </div>
        </div>

        {/* Scan Marker */}
        <div
          className="absolute w-4 h-4 bg-cyan-400 rounded-full border-2 border-cyan-300 shadow-lg"
          style={{
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            cursor: 'pointer'
          }}
          title={`Scan Location: ${scan.latitude}, ${scan.longitude}`}
        />
      </div>

      {/* Legend */}
      <div className="p-3 bg-slate-800 border-t border-slate-700">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded" />
            <span className="text-slate-400">High Confidence</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded" />
            <span className="text-slate-400">Medium Confidence</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded" />
            <span className="text-slate-400">Low Confidence</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 3D Subsurface Visualization Component
 * Displays subsurface layers and predicted mineral locations
 */
export const SubsurfaceVisualization: React.FC<VisualizationProps> = ({ scan, vizData3D }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [depth, setDepth] = useState(500);

  useEffect(() => {
    if (canvasRef.current) {
      drawSubsurface();
    }
  }, [depth, scan.results]);

  const drawSubsurface = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw subsurface layers
    const layerCount = 5;
    const layerHeight = canvas.height / layerCount;

    for (let i = 0; i < layerCount; i++) {
      const y = i * layerHeight;
      const intensity = 0.3 + (i / layerCount) * 0.4;

      ctx.fillStyle = `rgba(100, 150, 200, ${intensity})`;
      ctx.fillRect(0, y, canvas.width, layerHeight);

      // Add layer lines
      ctx.strokeStyle = 'rgba(150, 180, 220, 0.3)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();

      // Add depth label
      ctx.fillStyle = 'rgba(200, 220, 255, 0.6)';
      ctx.font = '10px monospace';
      ctx.fillText(`${(i * depth) / layerCount}m`, 5, y + 15);
    }

    // Draw predicted mineral indicators (if results available)
    if (scan.results?.pinn) {
      drawMineralIndicators(ctx, canvas, scan.results.pinn);
    }
  };

  const drawMineralIndicators = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement, pinnResults: any) => {
    // Placeholder: Draw sample mineral indicators
    const indicators = [
      { x: 0.3, y: 0.4, confidence: 0.85, color: '#fbbf24' }, // Gold-yellow
      { x: 0.6, y: 0.6, confidence: 0.72, color: '#10b981' }, // Lithium-green
      { x: 0.4, y: 0.7, confidence: 0.68, color: '#ef4444' }  // Copper-red
    ];

    indicators.forEach(indicator => {
      const x = canvas.width * indicator.x;
      const y = canvas.height * indicator.y;
      const radius = 8 * indicator.confidence;

      // Draw glow effect
      ctx.fillStyle = indicator.color.replace(')', ', 0.2)').replace('rgb', 'rgba');
      ctx.beginPath();
      ctx.arc(x, y, radius * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // Draw indicator
      ctx.fillStyle = indicator.color;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();

      // Draw border
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    });
  };

  return (
    <div className="w-full bg-slate-900 rounded-lg overflow-hidden">
      <div className="bg-slate-800 p-3 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">3D Subsurface Model</h3>
          </div>
          <div className="text-xs text-slate-400">
            Depth: {depth.toLocaleString()}m
          </div>
        </div>
      </div>

      {/* 3D Canvas */}
      <canvas
        ref={canvasRef}
        width={600}
        height={300}
        className="w-full h-64 bg-slate-950"
      />

      {/* Depth Slider */}
      <div className="p-3 bg-slate-800 border-t border-slate-700">
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 whitespace-nowrap">Max Depth:</label>
          <input
            type="range"
            min="100"
            max="2000"
            step="100"
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="flex-1"
          />
          <span className="text-xs text-slate-300 w-20 text-right">{depth}m</span>
        </div>
      </div>

      {/* Mineral Legend */}
      <div className="p-3 bg-slate-800 border-t border-slate-700">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full" />
            <span className="text-slate-400">Gold (Au)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full" />
            <span className="text-slate-400">Lithium (Li)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full" />
            <span className="text-slate-400">Copper (Cu)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Analysis Results Summary Component
 * Displays PINN, USHE, and TMAL analysis results
 */
export const AnalysisResultsSummary: React.FC<VisualizationProps> = ({ scan }) => {
  const [expandedResult, setExpandedResult] = useState<'pinn' | 'ushe' | 'tmal' | null>(null);

  const ResultCard: React.FC<{
    title: string;
    icon: React.ReactNode;
    color: string;
    data?: any;
    status?: string;
  }> = ({ title, icon, color, data, status }) => (
    <div className={`bg-slate-800 rounded-lg p-4 border-l-4 ${color}`}>
      <button
        onClick={() => setExpandedResult(expandedResult === title.toLowerCase() as any ? null : title.toLowerCase() as any)}
        className="w-full flex items-center justify-between mb-2 hover:opacity-80"
      >
        <div className="flex items-center gap-2">
          {icon}
          <h4 className="font-semibold text-white text-sm">{title}</h4>
        </div>
        <span className="text-xs px-2 py-1 bg-slate-700 rounded">
          {status || 'pending'}
        </span>
      </button>

      {expandedResult === title.toLowerCase() && data && (
        <div className="mt-2 pt-2 border-t border-slate-700">
          <div className="text-xs text-slate-300 space-y-1">
            {Object.entries(data).slice(0, 5).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-slate-500">{key}:</span>
                <span className="text-slate-200">{String(value).substring(0, 30)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="w-full">
      <h3 className="text-sm font-semibold text-white mb-3">Analysis Results</h3>
      <div className="grid grid-cols-3 gap-3">
        <ResultCard
          title="PINN"
          icon={<Zap className="w-4 h-4" />}
          color="border-cyan-400"
          data={scan.results?.pinn}
          status={scan.results?.pinn ? 'completed' : 'pending'}
        />
        <ResultCard
          title="USHE"
          icon={<AlertCircle className="w-4 h-4" />}
          color="border-amber-400"
          data={scan.results?.ushe}
          status={scan.results?.ushe ? 'completed' : 'pending'}
        />
        <ResultCard
          title="TMAL"
          icon={<Map className="w-4 h-4" />}
          color="border-emerald-400"
          data={scan.results?.tmal}
          status={scan.results?.tmal ? 'completed' : 'pending'}
        />
      </div>
    </div>
  );
};

/**
 * Combined Visualization Dashboard
 * Shows 2D map, 3D subsurface, and analysis results together
 */
export const ScanResultsVisualization: React.FC<VisualizationProps> = (props) => {
  return (
    <div className="w-full space-y-4">
      {/* Top row: Map visualization */}
      <MapVisualization {...props} />

      {/* Middle row: 3D subsurface + Analysis results */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <SubsurfaceVisualization {...props} />
        </div>
        <div>
          <AnalysisResultsSummary {...props} />
        </div>
      </div>
    </div>
  );
};
