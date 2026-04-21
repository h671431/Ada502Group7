# Introduction

FireGuard is a cloud-based services for predicting fire risk based on weather data. 
The system uses a Fire Risk Computation model (FRCM) to calculate fire risk based on environmental conditions. 

# System Overview
The system consists of
- Fire Risk Computation Model (implemented)
- Weather data input ()
- REST API (partial)
- Cloud hosting on NREC
- Landing page

# Current implementation
Implemented:
-

Partially:
- 

Planned:
- 

# How to run
'uv' needs to be installed

>uv run python src/frcm/__main__.py/bergen_2026_01_09.csv

This runs the Fire Risk Computaion Model on weather data and outputs fire risk predictions

# Landing Page
The FireGuard landing page is hosted on NREC:
>http://

# Architecture
Weather Data (CSV /MET API) -> FireGuard Service (planned API) -> Fire Risk Model (FRCM) -> Fire Risk Output

# Fire Risk Model
The Fire Risk Computation Model calculates fire risk based on:
- Temperature

# Technologies

# Future work
Store data in database
Implement authentication and authorization

# Team
Group 7: Hannah, benjamin and Mathias 