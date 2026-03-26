from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import logging

from frcm.datacontroller import fetch_met_forecast, fetch_met_latest
from frcm.datamodel.model import WeatherData, WeatherDataPoint
from frcm.fireriskmodel.compute import compute

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FireGuard API", version="0.1.0")

# MET API configuration
MET_API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
MET_HEADERS = {
    "User-Agent": "FireGuard/0.1.0 (https://github.com/Ada502Group7/frcm)"
}


@app.get("/", response_class=HTMLResponse)
def landing_page():
    return """
    <html lang="no">
<head>
    <meta charset="UTF-8">
    <title>FireGuard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 20px auto; padding: 20px; }
        h1 { color: #c0392b; }
        .container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        #map { height: 500px; border: 1px solid #ccc; }
        .info-panel { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        input[type="text"] { padding: 8px; width: 100%; font-size: 14px; margin: 5px 0; }
        button { 
            padding: 10px 20px; 
            background-color: #c0392b; 
            color: white; 
            border: none; 
            cursor: pointer; 
            border-radius: 3px;
            width: 100%;
            margin-top: 10px;
        }
        button:hover { background-color: #a93226; }
        .result { 
            margin-top: 20px; 
            padding: 15px; 
            background: #e8f4f8; 
            border-left: 4px solid #c0392b;
            border-radius: 3px;
            display: none;
        }
        .result.show { display: block; }
        .error { background: #ffe8e8; border-left-color: #c0392b; }
    </style>
</head>
<body>
    <h1>🔥 FireGuard</h1>
    <p>Brannrisiko-prognose for Norge basert på værdata fra MET.no</p>
    
    <div class="container">
        <div>
            <h2>Kart - Klikk for å velge lokasjon</h2>
            <div id="map"></div>
            <p style="font-size: 12px; color: #666; margin-top: 10px;">
                Klikk på kartet for å velge en lokasjon og hente værdata
            </p>
        </div>
        
        <div class="info-panel">
            <h2>Lokasjon</h2>
            <div>
                <label>Breddegrad (lat):</label>
                <input type="number" id="latitude" placeholder="f.eks. 60.3" step="0.001" readonly />
            </div>
            
            <div>    
                <label>Lengdegrad (lon):</label>
                <input type="number" id="longitude" placeholder="f.eks. 5.3" step="0.001" readonly />
                
                <button onclick="fetchWeather()">Hent værdata</button>
            </div>
            
            <div id="result" class="result">
                <h3>Værdata</h3>
                <p><strong>Tid:</strong> <span id="result-time"></span></p>
                <p><strong>Temperatur:</strong> <span id="result-temp"></span>°C</p>
                <p><strong>Relativ fuktighet:</strong> <span id="result-humidity"></span>%</p>
                <p><strong>Vindhastighet:</strong> <span id="result-wind"></span> m/s</p>
            </div>
        </div>
    </div>

    <script>
        // Initialize map centered on Norway
        const map = L.map('map').setView([60.5, 10.5], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(map);

        let marker = null;

        // Handle map clicks
        map.on('click', function(e) {
            const lat = e.latlng.lat.toFixed(6);
            const lon = e.latlng.lng.toFixed(6);
            
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lon;
            
            // Update marker
            if (marker) {
                map.removeLayer(marker);
            }
            marker = L.marker([lat, lon]).addTo(map)
                .bindPopup(`Lokasjon: ${lat}, ${lon}`)
                .openPopup();
        });

        async function fetchWeather() {
            const lat = document.getElementById('latitude').value;
            const lon = document.getElementById('longitude').value;
            const alt = document.getElementById('altitude').value;
            
            if (!lat || !lon) {
                alert('Vennligst velg en lokasjon på kartet');
                return;
            }
            
            try {
                const url = `/api/weather/latest?latitude=${lat}&longitude=${lon}${alt ? '&altitude=' + alt : ''}`;
                const response = await fetch(url);
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Feil ved henting av værdata');
                }
                
                const data = await response.json();
                const weather = data.weather;
                
                document.getElementById('result-time').textContent = new Date(weather.timestamp).toLocaleString('no-NO');
                document.getElementById('result-temp').textContent = weather.temperature.toFixed(1);
                document.getElementById('result-humidity').textContent = weather.humidity.toFixed(1);
                document.getElementById('result-wind').textContent = weather.wind_speed.toFixed(1);
                
                document.getElementById('result').classList.add('show');
            } catch (error) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = `<p class="error"><strong>Feil:</strong> ${error.message}</p>`;
                resultDiv.classList.add('show', 'error');
            }
        }
    </script>

</body>
</html>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/weather")
async def get_weather(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    altitude: Optional[float] = Query(None, description="Altitude in meters"),
    days: int = Query(7, ge=1, le=14, description="Number of days to fetch (1-14)")
):
    """Fetch weather data from MET.no based on coordinates and altitude."""

    try:
        logger.info(f"Fetching weather data for lat={latitude}, lon={longitude}, alt={altitude}")
        weather_points = await fetch_met_forecast(latitude, longitude, altitude=altitude, days=days)

        return {
            "location": {"latitude": latitude, "longitude": longitude, "altitude": altitude},
            "data_points": len(weather_points),
            "weather": weather_points,
        }

    except ValueError as e:
        logger.error(f"Data error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/weather/latest")
async def get_weather_latest(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    altitude: Optional[float] = Query(None, description="Altitude in meters"),
):
    """Fetch the most recent weather observation from MET.no."""

    try:
        logger.info(f"Fetching latest weather for lat={latitude}, lon={longitude}, alt={altitude}")
        weather_point = await fetch_met_latest(latitude, longitude, altitude=altitude)

        return {
            "location": {"latitude": latitude, "longitude": longitude, "altitude": altitude},
            "weather": weather_point,
        }

    except ValueError as e:
        logger.error(f"Data error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@app.get("/api/forecast")
async def get_forecast(
    latitude: Optional[float] = Query(None, description="Latitude"),
    longitude: Optional[float] = Query(None, description="Longitude"),
    location: Optional[str] = Query(None, description="Location name (Oslo, Bergen, etc.)")
):
    """
    Get fire risk forecast for a location.
    Accepts either coordinates or common location names.
    """
    # Common Norwegian locations
    locations_map = {
        "oslo": {"lat": 59.9139, "lon": 10.7522},
        "bergen": {"lat": 60.3913, "lon": 5.3221},
        "stavanger": {"lat": 58.9700, "lon": 5.7331},
        "trondheim": {"lat": 63.4305, "lon": 10.3951},
        "tromsø": {"lat": 69.6492, "lon": 18.9553},
    }
    
    # Resolve coordinates
    if latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    elif location:
        location_lower = location.lower()
        if location_lower in locations_map:
            coords = locations_map[location_lower]
            lat, lon = coords["lat"], coords["lon"]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown location: {location}. Supported: {', '.join(locations_map.keys())}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either (latitude, longitude) or location name"
        )
    
    try:
        # Fetch weather data
        weather_response = await get_weather(latitude=lat, longitude=lon)
        weather_data = weather_response["weather"]
        
        # Convert to WeatherData format
        from frcm.datamodel.utils import list_to_wdps
        data_points = list_to_wdps(weather_data)
        weather_obj = WeatherData(data=data_points)
        
        # Calculate fire risk
        fire_risk = compute(weather_obj)
        
        logger.info(f"Successfully computed fire risk for {location or f'({lat}, {lon})'}")
        
        return {
            "location": location or f"({lat}, {lon})",
            "latitude": lat,
            "longitude": lon,
            "forecast": [
                {
                    "timestamp": risk.timestamp.isoformat(),
                    "ttf": risk.ttf
                }
                for risk in fire_risk.firerisks
            ]
        }
    
    except Exception as e:
        logger.error(f"Error computing forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error computing forecast: {str(e)}")
