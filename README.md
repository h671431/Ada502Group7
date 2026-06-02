# Introduction
FireGuard is a cloud-based service for predicting fire risk based on weather data. 
The system uses a Fire Risk Computation Model (FRCM) to calculate fire risk based on environmental conditions. 

# System Overview
The system consists of:
- Fire Risk Computation Model 
- Weather data input (CSV or MET API)
- REST API 
- Cloud hosting on NREC
- Landing page
- Web application (UI +API) accessible via browser

# Current implementation
Implemented:
- Fire Risk Computation Model (FRCM) core calculation logic
- Weather data model with CSV parsing
- Command-line interface for fire risk computation
- Data preprocessing and utilities
- REST API with FastAPI (fully functional endpoints)
- MET API integration for weather forecast data
- Interactive landing page with map-based location selection
- Real-time fire risk calculation through web UI

Planned:
- Database integration for storing fire risk predictions
- Message broker for event-driven architecture
- Authentication and authorization system 

# How to run

**Command-line interface:**
`uv` needs to be installed
```
uv run python src/frcm/__main__.py bergen_2026_01_09.csv
```
This runs the Fire Risk Computation Model on weather data and outputs fire risk predictions.

**Web service:**
```
uv run python src/frcm/__main__.py
```
Starts the REST API server with interactive landing page at http://localhost:8000/

# Architecture

FireGuard is a multi-interface system for fire risk prediction:

```
Data Sources:
  CSV File ──────┐
                 ├─→ Fire Risk Computation Model (FRCM)
  MET API ───────┤
                 └─→ Fire Risk Output

Interfaces:
  1. Command-line:
     $ uv run python src/frcm/__main__.py <csv_file> [output_file]

  2. REST API Server (http://localhost:8000):
     ├─ GET /api/weather?latitude=X&longitude=Y - Fetch weather forecast
     ├─ GET /api/weather/latest?latitude=X&longitude=Y - Latest observation
     └─ GET /api/forecast?latitude=X&longitude=Y - Fire risk forecast (uses FRCM)

  3. Web UI:
     ├─ Interactive map at /
     ├─ Click to select location
     └─ Displays fire risk visualization with TTF values
```

**Data flow:**
1. Weather data sources (CSV or MET API) are fetched
2. Data controller normalizes weather data
3. Fire Risk Model computes risk based on temperature, humidity, wind, and TTF parameters
4. Results are returned via CLI, REST API, or web UI

# Fire Risk Model
The Fire Risk Computation Model calculates fire risk based on:
- Temperature
- Wind
- Rain

These parameters are used together with the TTF-computation to calculate a fire risk for a selected location/coordinate.
# Technologies
- **Python 3.13+** - Core language
- **FastAPI** - REST API framework
- **Uvicorn** - ASGI web server
- **Pydantic** - Data validation and modeling
- **NumPy** - Numerical computation for fire risk calculations
- **httpx** - HTTP client for MET API integration
- **Docker & Docker Compose** - Containerization
- **NREC** - Cloud hosting platform

# Future work
- Implement broker/subscription system for real-time alerts
- Store fire risk predictions in database for historical analysis
- Implement authentication and authorization for API endpoints
- Integrate with additional weather data sources
- Create a web dashboard for visualizing fire risk predictions

# CI/CD pipeline
This project uses GitHub Actions for continuous integration and deployment.

The pipeline is triggered on push to the main branch and performs:
- Build and validation of the project
- Secure SSH connection to the NREC server
- Pulling the latest code
- Rebuilding and restarting Docker containers

This ensures that the deployed application is automatically updated when changes are pushed. 

# Team
Group 7: Hannah, Benjamin, and Mathias 
