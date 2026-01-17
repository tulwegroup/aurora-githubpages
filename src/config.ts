
// Aurora OSI v3 - Global Infrastructure Configuration

const ENV = (import.meta as any).env || {};

export const APP_CONFIG = {
    // Detect environment
    MODE: ENV.MODE || 'production',
    
    API: {
        // In production (Railway): Use /api relative path, server.js proxies to localhost:8000
        // In development: Use localhost:8000 directly
        BASE_URL: ENV.MODE === 'production' ? '/api' : (ENV.VITE_API_URL || ENV.VITE_BACKEND_URL || 'http://localhost:8000'),
        
        // Infrastructure Details
        DB_PROVIDER: 'Neon Serverless Postgres',
        GEE_INTEGRATION: 'Server-Side (Railway Managed)',
        
        TIMEOUT_MS: 30000,
        POLLING_INTERVAL_MS: 3000
    },

    // Metadata for ConfigView UI
    INFRA: {
        IS_CUSTOM_ENDPOINT: !!ENV.VITE_BACKEND_URL,
        REGION: 'managed-auto'
    },

    FEATURES: {
        ENABLE_NEON_SYNC: true,
        ENABLE_RAILWAY_WORKERS: true,
        FORCE_HTTPS: true,
        STRICT_AUTH: true
    }
};
