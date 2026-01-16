import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { LeafletMouseEvent } from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface MapVisualizationProps {
  anomalies?: any[];
  onSelectAnomaly?: (anomaly: any) => void;
  selectedAnomaly?: any;
  centerCoordinates?: string;
  className?: string;
  isGEEActive?: boolean;
  showHistory?: boolean;
  campaign?: any;
}

// Fix for default markers
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const MapVisualization: React.FC<MapVisualizationProps> = ({
  anomalies = [],
  onSelectAnomaly = () => {},
  selectedAnomaly = null,
  centerCoordinates = '38.5,-117.5',
  className = '',
}) => {
  const parseCoordinates = (coords: string): [number, number] => {
    const parts = coords.split(',').map(p => parseFloat(p.trim()));
    return [parts[0], parts[1]];
  };

  const center = parseCoordinates(centerCoordinates);

  return (
    <div className={`relative bg-slate-900 ${className}`}>
      <MapContainer
        center={center}
        zoom={8}
        style={{ width: '100%', height: '100%', minHeight: '400px' }}
        className="z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        {anomalies.map((anomaly, idx) => (
          <Marker
            key={idx}
            position={[anomaly.lat, anomaly.lon]}
            eventHandlers={{
              click: () => onSelectAnomaly(anomaly)
            }}
          >
            <Popup>{anomaly.name || `Anomaly ${idx}`}</Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* GPS Coordinates Display */}
      <div className="absolute top-4 left-4 bg-black/70 backdrop-blur px-3 py-2 rounded text-xs font-mono text-emerald-400 border border-emerald-500/30 z-10">
        <div>Lat: {center[0].toFixed(6)}° N</div>
        <div>Lon: {center[1].toFixed(6)}° E</div>
      </div>
    </div>
  );
};

export default MapVisualization;
