# Introduction

FireGuard is a cloud-based services for predicting fire risk based on weather data. 
The system uses a Fire Risk Computation model (FRCM) to calculate fire risk based on environmental conditions. 

# System Overview
The system consists of:
- Fire Risk Computation Model (implemented)
- Weather data input (CSV or MET API)
- REST API (partial)
- Cloud hosting on NREC
- Landing page

# Current implementation
Implemented:
- Fire Risk Computation Model (FRCM) core calculation logic
- Weather data model with CSV parsing
- Command-line interface for fire risk computation
- Data preprocessing and utilities

Partially:
- REST API with FastAPI (endpoints available but still in development)
- MET API integration for weather forecast data
- Landing page served at /

Planned:
- Full cloud deployment on NREC
- Database integration for storing fire risk predictions
- Message broker for event-driven architecture
- Authentication and authorization system 

# How to run
'uv' needs to be installed

>uv run python src/frcm/__main__.py/bergen_2026_01_09.csv

This runs the Fire Risk Computaion Model on weather data and outputs fire risk predictions

# Landing Page
The FireGuard landing page is hosted on NREC:
>http://158.37.63.59:8000/

# Architecture
Weather Data (CSV /MET API) -> FireGuard Service (planned API) -> Fire Risk Model (FRCM) -> Fire Risk Output

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
- Add support for multiple regions and locations

# Team
Group 7: Hannah, Benjamin, and Mathias 