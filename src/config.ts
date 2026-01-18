
// Aurora OSI v3 - Global Infrastructure Configuration

const ENV = (import.meta as any).env || {};

export const APP_CONFIG = {
    // Detect environment - in production (Railway), always use /api
    MODE: ENV.MODE || 'production',
    
    API: {
        // Automatic detection (no manual config needed):
        // - Railway production: Always use /api (Express proxies to localhost:8000)
        // - localhost: Use http://localhost:8000 directly
        // Backend runs in same container, automatically proxied through Express
        BASE_URL: 'auto-detect',
        
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
