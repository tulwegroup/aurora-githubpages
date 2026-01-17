import React, { useState, useEffect, useCallback } from 'react';
import { Clock, Activity, CheckCircle, AlertCircle, Radio, TrendingUp } from 'lucide-react';

interface ScanStatusData {
    scan_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    metadata: {
        scan_type: string;
        location_description: string;
        minerals_requested: string[];
        scan_area_km2: number;
        pixel_count_total: number;
        detections_found: number;
        created_at: string;
        started_at?: string;
        completed_at?: string;
        confidence_average?: number;
    };
}

interface ScanStatusMonitorProps {
    scanId: string;
    isVisible: boolean;
}

const ScanStatusMonitor: React.FC<ScanStatusMonitorProps> = ({ scanId, isVisible }) => {
    const [scanData, setScanData] = useState<ScanStatusData | null>(null);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(0);

    const fetchScanStatus = useCallback(async () => {
        try {
            const response = await fetch(`/scans/${scanId}`);
            if (response.ok) {
                const data = await response.json() as any;
                setScanData(data as ScanStatusData);

                // Calculate elapsed time
                if (data.metadata.started_at) {
                    const startTime = new Date(data.metadata.started_at).getTime();
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    setElapsedTime(elapsed);

                    // Estimate time remaining based on progress
                    if (data.status === 'running' && data.metadata.pixel_count_total > 0) {
                        const progressPercent = (data.metadata.detections_found / Math.max(data.metadata.pixel_count_total, 1)) * 100;
                        if (progressPercent > 0 && progressPercent < 100) {
                            const timePerPercent = elapsed / progressPercent;
                            const estimated = Math.ceil((100 - progressPercent) * timePerPercent);
                            setEstimatedTimeRemaining(estimated);
                        }
                    }
                }
            }
        } catch (e) {
            console.error('Failed to fetch scan status:', e);
        }
    }, [scanId]);

    useEffect(() => {
        if (!isVisible) return;

        fetchScanStatus();
        const interval = setInterval(fetchScanStatus, 2000); // Poll every 2 seconds

        return () => clearInterval(interval);
    }, [scanId, isVisible, fetchScanStatus]);

    if (!isVisible || !scanData) {
        return null;
    }

    const progressPercent = scanData.metadata.pixel_count_total > 0
        ? (scanData.metadata.detections_found / scanData.metadata.pixel_count_total) * 100
        : 0;

    const formatTime = (seconds: number): string => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    };

    const getStatusIcon = () => {
        switch (scanData.status) {
            case 'completed':
                return <CheckCircle className="text-green-400" size={24} />;
            case 'running':
                return <Activity className="text-yellow-400 animate-pulse" size={24} />;
            case 'failed':
                return <AlertCircle className="text-red-400" size={24} />;
            default:
                return <Radio className="text-blue-400" size={24} />;
        }
    };

    const getStatusColor = () => {
        switch (scanData.status) {
            case 'completed':
                return 'from-green-900 to-green-800 border-green-500/30';
            case 'running':
                return 'from-yellow-900 to-yellow-800 border-yellow-500/30';
            case 'failed':
                return 'from-red-900 to-red-800 border-red-500/30';
            default:
                return 'from-blue-900 to-blue-800 border-blue-500/30';
        }
    };

    return (
        <div className={`bg-gradient-to-r ${getStatusColor()} rounded-lg p-6 border mb-8`}>
            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                    {getStatusIcon()}
                    <div>
                        <h3 className="text-lg font-bold text-white">
                            {scanData.status === 'completed' && '✓ Scan Complete'}
                            {scanData.status === 'running' && '🔍 Scan in Progress'}
                            {scanData.status === 'failed' && '✗ Scan Failed'}
                            {scanData.status === 'pending' && '⏳ Scan Pending'}
                        </h3>
                        <p className="text-sm text-slate-300 font-mono">{scanData.scan_id}</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-xs text-slate-400 mb-1">STATUS</p>
                    <p className="text-sm font-bold text-white uppercase">{scanData.status}</p>
                </div>
            </div>

            {/* Location and Minerals */}
            <div className="bg-black/30 rounded p-4 mb-4">
                <p className="text-xs text-slate-400 mb-1">TARGET AREA</p>
                <p className="text-white font-semibold mb-3">{scanData.metadata.location_description}</p>
                <p className="text-xs text-slate-400 mb-1">MINERALS</p>
                <p className="text-white">{scanData.metadata.minerals_requested.map(m => m.toUpperCase()).join(', ')}</p>
            </div>

            {/* Progress Bar */}
            {scanData.status !== 'completed' && scanData.status !== 'failed' && (
                <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                        <p className="text-xs text-slate-300 font-semibold">SCAN PROGRESS</p>
                        <p className="text-sm font-mono text-white">{Math.round(progressPercent)}%</p>
                    </div>
                    <div className="w-full bg-black/40 rounded-full h-3 overflow-hidden border border-slate-600">
                        <div
                            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
                            style={{ width: `${progressPercent}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Statistics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-black/40 rounded p-3 border border-slate-700">
                    <p className="text-xs text-slate-400 mb-1">PIXELS SCANNED</p>
                    <p className="text-lg font-bold text-white">{scanData.metadata.pixel_count_total.toLocaleString()}</p>
                </div>

                <div className="bg-black/40 rounded p-3 border border-slate-700">
                    <p className="text-xs text-slate-400 mb-1">DETECTIONS</p>
                    <p className={`text-lg font-bold ${scanData.metadata.detections_found > 0 ? 'text-green-400' : 'text-slate-400'}`}>
                        {scanData.metadata.detections_found}
                    </p>
                </div>

                <div className="bg-black/40 rounded p-3 border border-slate-700">
                    <p className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                        <Clock size={12} /> ELAPSED
                    </p>
                    <p className="text-lg font-bold text-white font-mono">{formatTime(elapsedTime)}</p>
                </div>

                <div className="bg-black/40 rounded p-3 border border-slate-700">
                    <p className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                        <TrendingUp size={12} /> ETA
                    </p>
                    <p className="text-lg font-bold text-white font-mono">
                        {scanData.status === 'running' && estimatedTimeRemaining > 0
                            ? formatTime(estimatedTimeRemaining)
                            : scanData.status === 'completed'
                            ? 'Done'
                            : '—'}
                    </p>
                </div>
            </div>

            {/* Scan Details */}
            <div className="bg-black/40 rounded p-4 border border-slate-700 text-sm">
                <div className="grid grid-cols-2 gap-3 text-slate-300">
                    <div>
                        <p className="text-xs text-slate-500 uppercase">Scan Type</p>
                        <p className="font-semibold text-white">{scanData.metadata.scan_type.toUpperCase()}</p>
                    </div>
                    <div>
                        <p className="text-xs text-slate-500 uppercase">Area</p>
                        <p className="font-semibold text-white">{scanData.metadata.scan_area_km2.toFixed(1)} km²</p>
                    </div>
                    {scanData.metadata.confidence_average && (
                        <div>
                            <p className="text-xs text-slate-500 uppercase">Avg Confidence</p>
                            <p className="font-semibold text-white">{(scanData.metadata.confidence_average * 100).toFixed(1)}%</p>
                        </div>
                    )}
                    <div>
                        <p className="text-xs text-slate-500 uppercase">Detection Rate</p>
                        <p className="font-semibold text-white">{Math.round(progressPercent)}%</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScanStatusMonitor;
