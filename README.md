# Introduction
FireGuard is a cloud-based service for predicting fire risk based on weather data. 
The system uses a Fire Risk Computation Model (FRCM) to calculate fire risk based on environmental conditions. 

# System Overview
The system consists of:
- Fire Risk Computation Model (implemented)
- Weather data input (CSV or MET API)
- REST API (partial)
- Cloud hosting on NREC
- Landing page
- Web application (UI +API) accessible via browser

# Current implementation
Implemented:
- Fire Risk Computation Model (FRCM) core calculation logic
- Weather data model with CSV parsing
- Command-line interface for fire risk computation
- Data preprocessing and utilities

Partially:
- REST API with FastAPI (endpoints available but still in development)
- MET API integration for weather forecast data

Planned:
- Database integration for storing fire risk predictions
- Message broker for event-driven architecture
- Authentication and authorization system 

# How to run locally
Running the Web Application with Docker:
Docker and Docker Compose needs to be installed
>docker-compose up --build

This builds and starts the application using Docker Compose.

The web application will be available at:
http://localhost:8000

How to only run the Fire Risk Computation Model:

'uv' needs to be installed

>uv run python src/frcm/__main__.py ./bergen_2026_01_09.csv

This runs the Fire Risk Computation Model on weather data and outputs fire risk predictions

Note:
- The Docker setup runs the full web application
- The Fire Risk Model can also be run independently using uv
# Landing Page
The FireGuard Web Application (UI + API) hosted on NREC:
>http://158.37.63.59:8000/

# Architecture
Weather Data (CSV /MET API) 
-> FireGuard Service (planned API) 
-> Fire Risk Model (FRCM) 
-> Fire Risk Output

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