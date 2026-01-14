# Aurora OSI v3 - Testing Guide

## Quick Start

### Run All Tests
```bash
cd backend
pytest -v
```

### Run Specific Test Class
```bash
pytest -v backend/test_main.py::TestHealthEndpoints
```

### Run Specific Test
```bash
pytest -v backend/test_main.py::TestMineralDetection::test_detect_mineral_basic
```

### Run with Coverage Report
```bash
pip install pytest-cov
pytest --cov=backend --cov-report=html --cov-report=term-missing
```

### Run with Markers
```bash
# Only unit tests
pytest -m unit -v

# Only integration tests
pytest -m integration -v

# Skip slow tests
pytest -v -m "not slow"
```

## Test Organization

### Health & Status Tests
**File:** `test_main.py::TestHealthEndpoints`

Tests the `/health` endpoint which reports system operational status and component health.

**Key Tests:**
- Basic health check response
- Response format validation
- Component status verification

**Run:**
```bash
pytest -v backend/test_main.py::TestHealthEndpoints
```

---

### Mineral Detection Tests
**File:** `test_main.py::TestMineralDetection`

Tests the core `/detect/mineral` endpoint for mineral spectral detection.

**Key Tests:**
- Basic detection with required parameters
- Detection with optional date range
- Invalid mineral error handling
- Invalid coordinate validation
- Complete response structure validation

**Run:**
```bash
pytest -v backend/test_main.py::TestMineralDetection
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/detect/mineral \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -20.5,
    "longitude": 134.5,
    "mineral": "arsenopyrite",
    "sensor": "Sentinel-2"
  }'
```

---

### Minerals List Tests
**File:** `test_main.py::TestMineralsList`

Tests mineral listing endpoints for discovery of available minerals.

**Key Tests:**
- List all minerals
- List minerals by commodity (Gold, Copper, etc.)
- Invalid commodity error handling

**Run:**
```bash
pytest -v backend/test_main.py::TestMineralsList
```

---

### Digital Twin Tests
**File:** `test_main.py::TestDigitalTwin`

Tests 4D subsurface digital twin query endpoints.

**Key Tests:**
- Volume queries
- Resource estimate queries
- Drill site recommendations
- Regional status

**Run:**
```bash
pytest -v backend/test_main.py::TestDigitalTwin
```

**Query Types:**
- `volume`: Calculate volumetric resource
- `resource_estimate`: Estimate tonnage and properties
- `drill_sites`: Find optimal drilling locations
- `material_properties`: Get rock/fluid properties

---

### Satellite Tasking Tests
**File:** `test_main.py::TestSatelliteTasking`

Tests autonomous satellite data acquisition tasking.

**Key Tests:**
- Create optical satellite task
- Create SAR satellite task
- Retrieve task status
- Non-existent task error handling

**Run:**
```bash
pytest -v backend/test_main.py::TestSatelliteTasking
```

**Sensor Types:**
- `optical`: High-resolution optical (Planet, Maxar)
- `SAR`: Synthetic Aperture Radar (Capella, ICEYE)
- `thermal`: Thermal infrared
- `lidar`: LiDAR topography/structure

**Urgency Levels:**
- `standard`: 7-14 days
- `urgent`: 2-7 days
- `critical`: 24 hours (higher cost)

---

### Seismic Digital Twin Tests
**File:** `test_main.py::TestSeismic`

Tests 2D/3D seismic voxel data management.

**Key Tests:**
- Create seismic survey
- Retrieve voxel data at specific location
- Amplitude, impedance, porosity retrieval

**Run:**
```bash
pytest -v backend/test_main.py::TestSeismic
```

---

### Physics Constraint Tests
**File:** `test_main.py::TestPhysics`

Tests physics law enforcement and residual tracking.

**Key Tests:**
- Retrieve physics residuals
- Filter residuals by severity
- Enforce density gradient constraints
- Verify constraint application results

**Run:**
```bash
pytest -v backend/test_main.py::TestPhysics
```

---

### Quantum Acceleration Tests
**File:** `test_main.py::TestQuantum`

Tests quantum-assisted gravimetric inversion.

**Key Tests:**
- Small problem quantum inversion (simulator)
- Large problem quantum inversion (QAOA)
- Background task processing

**Run:**
```bash
pytest -v backend/test_main.py::TestQuantum
```

**Quantum Backends:**
- `simulator`: Classical tensor network simulator
- `qaoa`: Quantum Approximate Optimization Algorithm
- `annealing`: D-Wave quantum annealing

---

### Error Handling Tests
**File:** `test_main.py::TestErrorHandling`

Tests error handling and validation.

**Key Tests:**
- Missing required fields
- Invalid JSON
- Non-existent endpoints
- Wrong HTTP methods

**Run:**
```bash
pytest -v backend/test_main.py::TestErrorHandling
```

---

## Local Testing Setup

### 1. Start Backend Services
```bash
bash quick_start.sh
```

This starts:
- PostgreSQL database
- Redis cache
- FastAPI backend (http://localhost:8000)

### 2. Run Tests Against Local Server
```bash
# In another terminal
cd backend
pytest -v
```

### 3. View API Documentation
Open browser to:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 4. Manual API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test mineral detection
curl -X POST http://localhost:8000/detect/mineral \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -20.5,
    "longitude": 134.5,
    "mineral": "arsenopyrite",
    "sensor": "Sentinel-2"
  }'

# List minerals
curl http://localhost:8000/detect/minerals

# Query digital twin
curl -X POST http://localhost:8000/twin/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "volume",
    "depth_min_m": 0,
    "depth_max_m": 2000,
    "region": "Australia"
  }'
```

---

## Continuous Integration

### GitHub Actions (Recommended)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest backend/ -v --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Performance Testing

### Load Testing with Locust
```bash
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class AuroraOSIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task
    def detect_mineral(self):
        self.client.post("/detect/mineral", json={
            "latitude": -20.5,
            "longitude": 134.5,
            "mineral": "arsenopyrite",
            "sensor": "Sentinel-2"
        })
EOF

# Run load test
locust -f locustfile.py -u 10 -r 2 -t 1m http://localhost:8000
```

---

## Test Coverage

### Generate Coverage Report
```bash
pytest backend/ --cov=backend --cov-report=html
# Open htmlcov/index.html
```

### Target Coverage Goals
- **Overall:** ≥80%
- **Critical paths:** ≥95%
- **Edge cases:** ≥70%

---

## Debugging Tests

### Verbose Output
```bash
pytest -vv backend/test_main.py
```

### Print Debug Info
```bash
pytest -s backend/test_main.py  # -s = no capture, show prints
```

### Drop Into Debugger
```bash
# Add to test code:
import pdb; pdb.set_trace()

# Run with:
pytest --pdb backend/test_main.py
```

### Last Failed Tests
```bash
pytest --lf backend/  # Run last failed
pytest --ff backend/  # Run failed first, then others
```

---

## Database Testing

### Reset Test Database
```bash
# In backend/database.py, add:
async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
```

### Use Test Database URL
```python
# In test_main.py, override the DATABASE_URL
@pytest.fixture(scope="session", autouse=True)
def set_test_db():
    import os
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/aurora_osi_test"
```

---

## Common Issues

### Tests Pass Locally, Fail in CI
- Ensure environment variables match (use .env.example)
- Check timezone consistency
- Verify database migrations run before tests

### Flaky Tests
- Add proper wait times for async operations
- Use `@pytest.mark.timeout(10)` to catch infinite loops
- Mock external services (satellite data, quantum backends)

### Slow Tests
- Use fixtures to set up data once: `@pytest.fixture(scope="session")`
- Mock time-consuming operations
- Run slow tests separately: `pytest -m "not slow"`

---

## Mocking External Services

### Mock Satellite Data
```python
@pytest.fixture
def mock_earth_engine():
    with patch('main.ee.ImageCollection') as mock:
        mock.return_value.median.return_value.getInfo.return_value = {
            'B2': 0.1, 'B3': 0.15, 'B4': 0.2
        }
        yield mock
```

### Mock Quantum Backend
```python
@pytest.fixture
def mock_quantum():
    with patch('main.QuantumBackend') as mock:
        mock.return_value.solve.return_value = {
            'result': 0.85,
            'iterations': 100
        }
        yield mock
```

---

## Best Practices

1. **Name tests clearly:** `test_<function>_<scenario>_<expected_result>`
2. **Use fixtures for setup:** Avoid duplicating setup code
3. **Mock external dependencies:** Don't rely on external services
4. **Test both success and failure:** Include error cases
5. **Keep tests fast:** Aim for <100ms per test
6. **Test one thing:** Each test should verify one behavior
7. **Use descriptive assertions:** Make failures clear

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated:** January 14, 2026  
**Maintained By:** Aurora OSI Development Team
