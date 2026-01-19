# Google Earth Engine (GEE) Setup Guide

Complete guide for setting up Google Earth Engine authentication and satellite data fetching in Aurora OSI v3.

## Overview

Aurora OSI integrates with Google Earth Engine to fetch real Sentinel-2 satellite imagery and elevation data for subsurface analysis. This guide walks through the authentication and configuration process.

## Prerequisites

- Google account
- Google Cloud Project
- Earth Engine API enabled
- Google Cloud Service Account with appropriate permissions

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** (e.g., `aurora-osi-v3`)

## Step 2: Enable Google Earth Engine API

1. In Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Earth Engine API"
3. Click on "Earth Engine API" and select **Enable**
4. Wait for the API to be enabled

## Step 3: Create a Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Fill in:
   - **Service Account Name**: `aurora-gee-integration`
   - **Service Account ID**: (auto-filled)
   - Click **Create and Continue**
4. On "Grant this service account access to project":
   - Add role: **Earth Engine** > **Earth Engine Service Account User**
   - Click **Continue**
5. Click **Done**

## Step 4: Create and Download Credentials JSON

1. In **APIs & Services** > **Credentials**, find your service account
2. Click on the service account email link
3. Go to the **Keys** tab
4. Click **Add Key** > **Create new key**
5. Choose **JSON** format
6. Click **Create** - a JSON file will download automatically

**Save this file securely** - you'll need it for authentication.

## Step 5: Register Service Account with Earth Engine

1. Note your service account email from the JSON credentials file:
   ```
   "client_email": "aurora-gee-integration@aurora-osi-v3.iam.gserviceaccount.com"
   ```

2. Go to [Google Earth Engine Signup](https://earthengine.google.com/signup/)

3. Sign in and go to **Edit Profile** > **Developers**

4. Add your service account email to the whitelist

5. Wait for approval (usually immediate, but can take 24 hours)

## Step 6: Configure Aurora OSI with Credentials

### Option A: Environment Variable (Recommended for Production)

1. Store the JSON credentials file in a secure location:
   ```bash
   mkdir -p /secure/gee-credentials
   cp /path/to/downloaded-file.json /secure/gee-credentials/aurora-gee.json
   chmod 600 /secure/gee-credentials/aurora-gee.json
   ```

2. Set the environment variable:
   ```bash
   export GEE_CREDENTIALS="/secure/gee-credentials/aurora-gee.json"
   ```

3. In your `.env` file (production):
   ```
   GEE_CREDENTIALS=/secure/gee-credentials/aurora-gee.json
   ```

### Option B: API Endpoint (Development)

Send a POST request to initialize GEE with credentials path:
```bash
curl -X POST http://localhost:8000/gee/initialize \
  -H "Content-Type: application/json" \
  -d '{"credentials_path": "/path/to/aurora-gee.json"}'
```

Response:
```json
{
  "success": true,
  "message": "Google Earth Engine authenticated"
}
```

## Step 7: Test the Integration

### Initialize GEE Authentication

```bash
curl -X POST http://localhost:8000/gee/initialize \
  -H "Content-Type: application/json" \
  -d {}
```

Response (success):
```json
{
  "success": true,
  "message": "Google Earth Engine authenticated"
}
```

### Fetch Sentinel-2 Data

```bash
curl -X POST http://localhost:8000/gee/sentinel2 \
  -H "Content-Type: application/json" \
  -d {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_m": 5000,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "max_cloud_cover": 0.2
  }
```

Response (success):
```json
{
  "success": true,
  "data": {
    "bands": {
      "B2": 1234.5,
      "B3": 2345.6,
      "B4": 3456.7,
      "B8": 4567.8,
      "B11": 5678.9,
      "B12": 6789.0
    },
    "metadata": {
      "product_id": "S2A_MSIL2A_20240115T123456_N0510_R014_T48TVT_20240115T154639",
      "acquisition_date": "2024-01-15T12:34:56Z",
      "cloud_coverage": 0.05,
      "spatial_resolution_m": 10,
      "crs": "EPSG:4326"
    },
    "image_id": "COPERNICUS/S2_SR/20240115T123456_20240115T124518_T48TVT",
    "geometry": {...}
  }
}
```

### Fetch DEM Data

```bash
curl -X POST http://localhost:8000/gee/dem \
  -H "Content-Type: application/json" \
  -d {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_m": 5000
  }
```

Response (success):
```json
{
  "success": true,
  "data": {
    "elevation": {
      "elevation_min": 0.5,
      "elevation_max": 245.3,
      "elevation_mean": 45.2,
      "elevation_median": 38.1,
      "elevation_stdDev": 52.4
    },
    "metadata": {
      "dataset": "USGS 3DEP 10m",
      "resolution_m": 10,
      "crs": "EPSG:4326"
    }
  }
}
```

### Calculate Spectral Indices

```bash
curl -X POST http://localhost:8000/gee/spectral-indices \
  -H "Content-Type: application/json" \
  -d {
    "image_id": "COPERNICUS/S2_SR/20240115T123456_20240115T124518_T48TVT",
    "roi_geometry": {
      "type": "Point",
      "coordinates": [-74.0060, 40.7128]
    }
  }
```

Response (success):
```json
{
  "success": true,
  "indices": {
    "ndvi": 0.45,
    "ndii": 0.23,
    "sr": 3.2
  }
}
```

## API Endpoints Reference

### 1. Initialize GEE Authentication

**Endpoint:** `POST /gee/initialize`

**Request:**
```json
{
  "credentials_path": "/path/to/gee-credentials.json"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Google Earth Engine authenticated"
}
```

### 2. Fetch Sentinel-2 Data

**Endpoint:** `POST /gee/sentinel2`

**Request:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_m": 5000,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "max_cloud_cover": 0.2
}
```

**Parameters:**
- `latitude` (required): Target latitude
- `longitude` (required): Target longitude
- `radius_m` (optional, default: 5000): Search radius in meters
- `start_date` (optional, default: 30 days ago): ISO format start date
- `end_date` (optional, default: today): ISO format end date
- `max_cloud_cover` (optional, default: 0.2): Maximum cloud cover (0-1)

**Response:**
```json
{
  "success": true,
  "data": {
    "bands": {
      "B2": float,  // Blue band
      "B3": float,  // Green band
      "B4": float,  // Red band
      "B8": float,  // NIR band
      "B11": float, // SWIR 1 band
      "B12": float  // SWIR 2 band
    },
    "metadata": {
      "product_id": "string",
      "acquisition_date": "ISO format",
      "cloud_coverage": float,
      "spatial_resolution_m": 10,
      "crs": "EPSG:4326"
    },
    "image_id": "string",
    "geometry": {...}
  }
}
```

### 3. Fetch DEM Data

**Endpoint:** `POST /gee/dem`

**Request:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_m": 5000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "elevation": {
      "elevation_min": float,
      "elevation_max": float,
      "elevation_mean": float,
      "elevation_median": float,
      "elevation_stdDev": float
    },
    "metadata": {
      "dataset": "USGS 3DEP 10m",
      "resolution_m": 10,
      "crs": "EPSG:4326"
    }
  }
}
```

### 4. Calculate Spectral Indices

**Endpoint:** `POST /gee/spectral-indices`

**Request:**
```json
{
  "image_id": "COPERNICUS/S2_SR/...",
  "roi_geometry": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  }
}
```

**Response:**
```json
{
  "success": true,
  "indices": {
    "ndvi": float,  // Normalized Difference Vegetation Index
    "ndii": float,  // Normalized Difference Iron Index (mineral detection)
    "sr": float     // Spectral Ratio (geological features)
  }
}
```

## Bands Reference

### Sentinel-2 Bands Used in Aurora OSI

| Band | Wavelength (nm) | Resolution | Use |
|------|-----------------|-----------|-----|
| B2   | 490             | 10m       | Blue (water/atmospheric) |
| B3   | 560             | 10m       | Green (vegetation reference) |
| B4   | 665             | 10m       | Red (mineral absorption) |
| B8   | 842             | 10m       | NIR (vegetation strength) |
| B11  | 1610            | 20m       | SWIR (mineral diagnostic) |
| B12  | 2190            | 20m       | SWIR (geological features) |

### Spectral Indices for Mineral Detection

| Index | Formula | Meaning |
|-------|---------|---------|
| NDVI  | (B8 - B4) / (B8 + B4) | Vegetation presence; mineralogy in bare areas |
| NDII  | (B8 - B11) / (B8 + B11) | Iron oxide detection; mining indicators |
| SR    | B8 / B4 | Simple ratio; mineral spectral properties |

## Troubleshooting

### Error: "GEE_CREDENTIALS environment variable not set"

**Solution:**
1. Ensure the JSON credentials file is saved
2. Set the environment variable:
   ```bash
   export GEE_CREDENTIALS="/path/to/credentials.json"
   ```
3. Verify the path exists:
   ```bash
   ls -la $GEE_CREDENTIALS
   ```

### Error: "Service account not registered with Earth Engine"

**Solution:**
1. Verify your service account email from the JSON file
2. Go to [Earth Engine Signup](https://earthengine.google.com/signup/)
3. Add the service account email to the whitelist
4. Wait 24 hours for approval

### Error: "No Sentinel-2 data available"

**Possible causes:**
- Location has no Sentinel-2 coverage (valid for most of the world, but not all)
- Date range is too narrow or in the past
- Cloud cover threshold is too strict

**Solution:**
1. Try a different date range (at least 30 days)
2. Increase `max_cloud_cover` to 0.5 or higher
3. Verify the location is covered by Sentinel-2 (global coverage except polar regions)

### Error: "Invalid credentials"

**Solution:**
1. Regenerate the JSON credentials file
2. Ensure you're using a valid service account (not a regular user account)
3. Check that the service account has the "Earth Engine Service Account User" role
4. Verify the JSON file is not corrupted

## Security Best Practices

1. **Never commit credentials to git:**
   ```bash
   echo "gee-credentials.json" >> .gitignore
   ```

2. **Use environment variables for production:**
   ```bash
   export GEE_CREDENTIALS="/secure/path/credentials.json"
   ```

3. **Restrict file permissions:**
   ```bash
   chmod 600 /path/to/gee-credentials.json
   ```

4. **Rotate credentials regularly:**
   - Delete old keys in Google Cloud Console
   - Create new ones every 90 days

5. **Monitor GEE API usage:**
   - Check [Earth Engine Statistics](https://earthengine.google.com/api_docs/overview/)
   - Set quotas in Google Cloud Console

## Integration with Aurora OSI Workflows

### Workflow 1: Real-Time Satellite Data for New Scans

```
1. User creates new scan in MissionControl (latitude, longitude)
2. Aurora OSI calls POST /gee/sentinel2 with scan coordinates
3. Backend fetches real Sentinel-2 data
4. Data stored in database with scan results
5. PINN/USHE/TMAL analysis runs on real satellite data
6. Visualization displays satellite base layer with analysis results
```

### Workflow 2: Mineral Detection via Spectral Analysis

```
1. Sentinel-2 data fetched via /gee/sentinel2
2. Image ID extracted from response
3. POST /gee/spectral-indices called with image ID
4. NDII (iron index) calculated for mineral detection
5. Results passed to PINN model for prediction
6. High-confidence minerals highlighted on map
```

### Workflow 3: Digital Twin Integration

```
1. DEM data fetched via /gee/dem for surface topography
2. Sentinel-2 bands provide spectral information
3. Combined data creates 3D digital twin
4. Subsurface layers rendered with mineral probabilities
5. User explores subsurface in interactive 3D view
```

## Performance Optimization

### API Quotas and Limits

Google Earth Engine has generous quotas for authenticated users:
- **Requests per day:** 10,000+
- **Pixels processed:** Essentially unlimited
- **Rate limit:** ~10 concurrent requests

### Optimization Tips

1. **Cache results:**
   ```python
   # Store GEE results in database
   # Avoid re-fetching the same area and date range
   ```

2. **Reduce processing area:**
   ```python
   # Use smaller radius_m (5000m instead of 50000m)
   # Reduces pixels processed and API response time
   ```

3. **Batch requests:**
   ```python
   # Process multiple scans in parallel
   # Earth Engine can handle concurrent requests
   ```

4. **Use appropriate resolution:**
   ```python
   # Sentinel-2 is 10m resolution
   # Use scale >= 10 to avoid unnecessary upsampling
   ```

## Next Steps

1. ✅ Set up Google Cloud Project and service account
2. ✅ Download credentials JSON file
3. ✅ Register service account with Earth Engine
4. ✅ Set GEE_CREDENTIALS environment variable
5. ✅ Test API endpoints with sample coordinates
6. ✅ Integrate GEE data with MissionControl scans
7. ✅ Configure visualization to display satellite base layer
8. ✅ Set up monitoring for GEE API usage

## Support & Resources

- [Google Earth Engine Documentation](https://developers.google.com/earth-engine)
- [Sentinel-2 User Guide](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi)
- [Earth Engine API Reference](https://developers.google.com/earth-engine/apidocs)
- [Aurora OSI API Documentation](./API_DOCUMENTATION.md)

## Contact

For issues or questions about Aurora OSI's GEE integration:
- GitHub Issues: [Aurora OSI Repository](https://github.com/your-org/aurora-osi)
- Documentation: [Architecture Guide](./ARCHITECTURE.md)
