
// Aurora OSI v3 - Global Infrastructure Configuration

const ENV = (import.meta as any).env || {};

export const APP_CONFIG = {
    // Detect environment
    MODE: ENV.MODE || 'production',
    
    API: {
        // Vercel/Vite environment variable with a hardcoded fallback for safety
        BASE_URL: ENV.VITE_API_URL || ENV.VITE_BACKEND_URL || 'https://aurora-osi-v4.up.railway.app',
        
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
