"""
Aurora OSI v3 - Main Application Tests
Comprehensive integration tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json

# Import the FastAPI app
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints"""
    
    def test_health_check(self):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "operational"
        assert "timestamp" in data
        assert "components" in data
        assert data["components"]["spectral_library"] == "operational"
        assert data["components"]["database"] == "operational"
    
    def test_health_check_response_format(self):
        """Verify health response has required fields"""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "components"]
        for field in required_fields:
            assert field in data


class TestMineralDetection:
    """Test mineral detection endpoints"""
    
    def test_detect_mineral_basic(self):
        """Test basic mineral detection"""
        response = client.post("/detect/mineral", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "mineral": "arsenopyrite",
            "sensor": "Sentinel-2"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["mineral"] == "arsenopyrite"
        assert "confidence_score" in data
        assert "confidence_tier" in data
        assert 0 <= data["confidence_score"] <= 1
        assert data["confidence_tier"] in ["TIER_0", "TIER_1", "TIER_2", "TIER_3"]
    
    def test_detect_mineral_with_dates(self):
        """Test detection with date range"""
        response = client.post("/detect/mineral", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "mineral": "chalcopyrite",
            "sensor": "Landsat8",
            "date_start": "2025-01-01",
            "date_end": "2026-01-14"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["mineral"] == "chalcopyrite"
    
    def test_detect_mineral_invalid_mineral(self):
        """Test detection with invalid mineral"""
        response = client.post("/detect/mineral", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "mineral": "invalid_mineral_xyz",
            "sensor": "Sentinel-2"
        })
        assert response.status_code == 404
    
    def test_detect_mineral_invalid_coordinates(self):
        """Test detection with invalid coordinates"""
        response = client.post("/detect/mineral", json={
            "latitude": 95.0,  # Invalid: > 90
            "longitude": 134.5,
            "mineral": "arsenopyrite",
            "sensor": "Sentinel-2"
        })
        assert response.status_code == 422  # Validation error
    
    def test_detect_mineral_response_structure(self):
        """Verify detection response has all required fields"""
        response = client.post("/detect/mineral", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "mineral": "quartz",
            "sensor": "Sentinel-2"
        })
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "mineral",
            "confidence_score",
            "confidence_tier",
            "detection_decision",
            "coordinates",
            "spectral_match_score",
            "depth_estimate_m",
            "processing_time_ms",
            "applied_corrections",
            "temporal_coherence",
            "recommendations"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestMineralsList:
    """Test mineral listing endpoints"""
    
    def test_list_minerals(self):
        """Test GET /detect/minerals endpoint"""
        response = client.get("/detect/minerals")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_minerals" in data
        assert "by_commodity" in data
        assert isinstance(data["by_commodity"], dict)
        assert len(data["by_commodity"]) > 0
    
    def test_list_minerals_commodity_gold(self):
        """Test listing Gold minerals"""
        response = client.get("/detect/commodity/Gold")
        assert response.status_code == 200
        
        data = response.json()
        assert data["commodity"] == "Gold"
        assert "minerals" in data
        assert len(data["minerals"]) > 0
        assert any(m["name"] == "arsenopyrite" for m in data["minerals"])
    
    def test_list_minerals_commodity_copper(self):
        """Test listing Copper minerals"""
        response = client.get("/detect/commodity/Copper")
        assert response.status_code == 200
        
        data = response.json()
        assert data["commodity"] == "Copper"
        assert "minerals" in data
        assert len(data["minerals"]) > 0
        assert any(m["name"] == "chalcopyrite" for m in data["minerals"])
    
    def test_list_minerals_invalid_commodity(self):
        """Test listing invalid commodity"""
        response = client.get("/detect/commodity/InvalidCommodity")
        assert response.status_code == 404


class TestDigitalTwin:
    """Test digital twin query endpoints"""
    
    def test_twin_query_volume(self):
        """Test digital twin volume query"""
        response = client.post("/twin/query", json={
            "query_type": "volume",
            "depth_min_m": 0,
            "depth_max_m": 2000,
            "region": "Australia"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["query_type"] == "volume"
        assert "result_count" in data
        assert "voxels" in data
        assert isinstance(data["voxels"], list)
    
    def test_twin_query_resource_estimate(self):
        """Test digital twin resource estimate query"""
        response = client.post("/twin/query", json={
            "query_type": "resource_estimate",
            "resource_type": "copper",
            "depth_min_m": 100,
            "depth_max_m": 1500,
            "confidence_min": 0.7,
            "region": "Australia"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["query_type"] == "resource_estimate"
        assert "estimated_resource_tonnes" in data
        assert "confidence_level" in data
    
    def test_twin_query_drill_sites(self):
        """Test digital twin drill site recommendation"""
        response = client.post("/twin/query", json={
            "query_type": "drill_sites",
            "resource_type": "gold",
            "depth_min_m": 50,
            "depth_max_m": 500,
            "region": "Australia"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["query_type"] == "drill_sites"
        assert "voxels" in data
    
    def test_twin_status(self):
        """Test getting digital twin status"""
        response = client.get("/twin/Australia/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["region"] == "Australia"
        assert data["status"] == "operational"
        assert "coverage_percent" in data
        assert "voxel_count" in data
        assert 0 <= data["coverage_percent"] <= 100


class TestSatelliteTasking:
    """Test satellite tasking endpoints"""
    
    def test_create_satellite_task(self):
        """Test creating satellite task"""
        response = client.post("/satellite/task", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "resolution_m": 3.0,
            "sensor_type": "optical",
            "urgency": "standard",
            "area_size_km2": 100.0
        })
        assert response.status_code == 201
        
        data = response.json()
        assert "task_id" in data
        assert data["sensor"] == "optical"
        assert data["resolution_m"] == 3.0
        assert data["status"] == "pending"
        assert data["estimated_cost_usd"] > 0
    
    def test_create_satellite_task_sar(self):
        """Test creating SAR satellite task"""
        response = client.post("/satellite/task", json={
            "latitude": 0.0,
            "longitude": 0.0,
            "resolution_m": 1.0,
            "sensor_type": "SAR",
            "urgency": "urgent",
            "area_size_km2": 50.0
        })
        assert response.status_code == 201
        
        data = response.json()
        assert data["sensor"] == "SAR"
        assert data["urgency"] == "urgent"
    
    def test_get_satellite_task(self):
        """Test retrieving satellite task"""
        # First create a task
        create_response = client.post("/satellite/task", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "resolution_m": 3.0,
            "sensor_type": "optical",
            "urgency": "standard",
            "area_size_km2": 100.0
        })
        assert create_response.status_code == 201
        
        task_id = create_response.json()["task_id"]
        
        # Now retrieve it
        get_response = client.get(f"/satellite/task/{task_id}")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["task_id"] == task_id
        assert "status" in data
        assert "created_at" in data
    
    def test_get_satellite_task_not_found(self):
        """Test retrieving non-existent task"""
        response = client.get("/satellite/task/INVALID_TASK_ID")
        assert response.status_code == 404


class TestSeismic:
    """Test seismic digital twin endpoints"""
    
    def test_create_seismic_survey(self):
        """Test creating seismic survey"""
        response = client.post("/seismic/survey", json={
            "survey_id": "SEIS_TEST_001",
            "inline_count": 500,
            "crossline_count": 750,
            "depth_samples": 4000,
            "depth_min_m": 0,
            "depth_max_m": 5000,
            "voxel_size_m": 12.5
        })
        assert response.status_code == 201
        
        data = response.json()
        assert data["survey_id"] == "SEIS_TEST_001"
        assert data["status"] == "created"
        assert data["voxel_count"] > 0
    
    def test_get_seismic_voxel(self):
        """Test retrieving seismic voxel data"""
        response = client.get("/seismic/SEIS_TEST_001/amplitude/250/375/2500")
        assert response.status_code == 200
        
        data = response.json()
        assert data["survey_id"] == "SEIS_TEST_001"
        assert data["inline"] == 250
        assert data["crossline"] == 375
        assert data["depth_m"] == 2500
        assert "amplitude" in data
        assert "impedance" in data
        assert "porosity" in data


class TestPhysics:
    """Test physics constraint endpoints"""
    
    def test_get_physics_residuals(self):
        """Test retrieving physics residuals"""
        response = client.get("/physics/residuals")
        assert response.status_code == 200
        
        data = response.json()
        assert "residual_count" in data
        assert "residuals" in data
        assert isinstance(data["residuals"], list)
    
    def test_get_physics_residuals_by_severity(self):
        """Test retrieving physics residuals by severity"""
        response = client.get("/physics/residuals?severity=high")
        assert response.status_code == 200
        
        data = response.json()
        assert "residuals" in data
    
    def test_enforce_physics_constraints(self):
        """Test enforcing physics constraints"""
        response = client.post("/physics/enforce", json={
            "constraint_type": "density_gradient",
            "parameter": "density",
            "min_value": 2000,
            "max_value": 3500,
            "physics_law": "lithostatic_gradient"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["constraint_applied"] == True
        assert "violations_corrected" in data


class TestQuantum:
    """Test quantum acceleration endpoints"""
    
    def test_quantum_inversion(self):
        """Test quantum gravimetric inversion"""
        response = client.post("/quantum/invert", json={
            "problem_size": 100,
            "num_qubits": 50,
            "quantum_backend": "simulator",
            "classical_preconditioning": True,
            "refinement_iterations": 3
        })
        assert response.status_code == 201
        
        data = response.json()
        assert "inversion_id" in data
        assert data["status"] == "processing"
        assert data["quantum_backend"] == "simulator"
        assert data["problem_size"] == 100
    
    def test_quantum_inversion_large_problem(self):
        """Test quantum inversion with large problem"""
        response = client.post("/quantum/invert", json={
            "problem_size": 10000,
            "num_qubits": 500,
            "quantum_backend": "qaoa",
            "classical_preconditioning": True,
            "refinement_iterations": 5
        })
        assert response.status_code == 201
        
        data = response.json()
        assert data["quantum_backend"] == "qaoa"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_required_field(self):
        """Test request with missing required field"""
        response = client.post("/detect/mineral", json={
            "latitude": -20.5,
            # Missing longitude, mineral, sensor
        })
        assert response.status_code == 422
    
    def test_invalid_json(self):
        """Test request with invalid JSON"""
        response = client.post(
            "/detect/mineral",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_endpoint_not_found(self):
        """Test accessing non-existent endpoint"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test wrong HTTP method"""
        response = client.get("/detect/mineral")  # Should be POST
        assert response.status_code == 405


class TestCORSHeaders:
    """Test CORS headers"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.get("/health")
        # FastAPI CORSMiddleware should add these
        assert response.status_code == 200


class TestResponseFormats:
    """Test response format consistency"""
    
    def test_error_response_format(self):
        """Test error responses have consistent format"""
        response = client.post("/detect/mineral", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "mineral": "nonexistent",
            "sensor": "Sentinel-2"
        })
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    def test_timestamp_format(self):
        """Test timestamps are ISO format"""
        response = client.get("/health")
        data = response.json()
        
        timestamp = data["timestamp"]
        # Should be valid ISO format
        assert "T" in timestamp
        assert "Z" in timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
