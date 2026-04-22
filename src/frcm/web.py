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
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FireGuard - Brannrisiko Prognose</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .wrapper { max-width: 1400px; margin: 0 auto; }
        h1 { 
            color: white; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle { 
            color: rgba(255,255,255,0.9); 
            margin-bottom: 30px;
            font-size: 14px;
        }
        .container { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px;
        }
        @media (max-width: 1024px) {
            .container { grid-template-columns: 1fr; }
        }
        .panel { 
            background: white; 
            border-radius: 10px; 
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .panel h2 { 
            color: #333; 
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        #map { 
            height: 500px; 
            border-radius: 8px;
            overflow: hidden;
        }
        label { 
            display: block; 
            margin-top: 15px;
            font-weight: 600;
            color: #333;
            font-size: 13px;
        }
        input[type="number"] { 
            padding: 10px; 
            width: 100%; 
            font-size: 14px; 
            margin-top: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            transition: border-color 0.3s;
        }
        input[type="number"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button { 
            padding: 12px 20px; 
            background-color: #667eea; 
            color: white; 
            border: none; 
            cursor: pointer; 
            border-radius: 4px;
            width: 100%;
            margin-top: 15px;
            font-weight: 600;
            transition: background-color 0.3s;
        }
        button:hover { background-color: #5568d3; }
        button:active { transform: scale(0.98); }
        
        .result-section { margin-top: 20px; }
        .result { 
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            display: none;
        }
        .result.show { display: block; }
        .result.error {
            background: #ffe8e8;
            border-left-color: #e74c3c;
        }
        
        .weather-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }
        .weather-item {
            background: white;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #eee;
        }
        .weather-item strong { color: #667eea; }
        .weather-item .value { font-size: 18px; font-weight: bold; }
        
        .firerisk-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
            text-align: center;
        }
        .ttf-value { 
            font-size: 28px; 
            font-weight: bold; 
            margin: 10px 0;
        }
        .ttf-label { 
            font-size: 12px; 
            opacity: 0.9;
            margin: 5px 0;
        }
        .risk-level {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
            margin-top: 10px;
        }
        .risk-high { background: #e74c3c; }
        .risk-medium { background: #f39c12; }
        .risk-low { background: #27ae60; }
        
        #forecastChart { margin-top: 20px; }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .loading.show { display: block; }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <h1>🔥 FireGuard</h1>
        <p class="subtitle">Brannrisiko-prognose for Norge basert på værdata fra MET.no</p>
        
        <div class="container">
            <div class="panel">
                <h2>Kart - Klikk for å velge lokasjon</h2>
                <div id="map"></div>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">
                    Klikk på kartet for å velge en lokasjon
                </p>
            </div>
            
            <div class="panel">
                <h2>Brannrisikoanalyse</h2>
                
                <label for="latitude">Breddegrad (lat):</label>
                <input type="number" id="latitude" placeholder="f.eks. 60.3" step="0.001" readonly />
                
                <label for="longitude">Lengdegrad (lon):</label>
                <input type="number" id="longitude" placeholder="f.eks. 5.3" step="0.001" readonly />
                
                <label for="altitude">Høyde (meter, valgfritt):</label>
                <input type="number" id="altitude" placeholder="f.eks. 50" step="1" />
                
                <button onclick="fetchWeatherAndRisk()">Beregn brannrisiko</button>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p style="margin-top: 10px; color: #333;">Beregner...</p>
                </div>
                
                <div id="weatherResult" class="result-section">
                    <div id="weatherDisplay" class="result">
                        <h3>Værdata</h3>
                        <div class="weather-grid">
                            <div class="weather-item">
                                <strong>Tid:</strong>
                                <div class="value" id="result-time">-</div>
                            </div>
                            <div class="weather-item">
                                <strong>Temperatur:</strong>
                                <div class="value" id="result-temp">-</div>
                            </div>
                            <div class="weather-item">
                                <strong>Fuktighet:</strong>
                                <div class="value" id="result-humidity">-</div>
                            </div>
                            <div class="weather-item">
                                <strong>Vind:</strong>
                                <div class="value" id="result-wind">-</div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="fireriskDisplay" class="result">
                        <h3>Brannrisiko</h3>
                        <div class="firerisk-item">
                            <div class="ttf-value" id="result-ttf">-</div>
                            <div id="result-risk-level" class="risk-level">-</div>
                        </div>
                        <p style="font-size: 12px; margin-top: 10px; color: #666;">
                            <strong>Tolkning:</strong> Lavere TTF = høyere brannrisiko. 
                            TTF &lt; 3 = høy risiko, TTF 3-6 = medium risiko, TTF &gt; 6 = lav risiko
                        </p>
                    </div>
                </div>
                
                <div id="errorResult" class="result error"></div>
            </div>
        </div>
        
        <div class="panel" style="margin-top: 20px;">
            <h2>7-dagars brannrisikoprognose</h2>
            <div style="position: relative; height: 300px;">
                <canvas id="forecastChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        let forecastChart = null;
        
        // Initialize map
        const map = L.map('map').setView([60.5, 10.5], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(map);

        let marker = null;

        map.on('click', function(e) {
            const lat = e.latlng.lat.toFixed(6);
            const lon = e.latlng.lng.toFixed(6);
            
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lon;
            
            if (marker) map.removeLayer(marker);
            marker = L.marker([lat, lon]).addTo(map)
                .bindPopup(`${lat}, ${lon}`)
                .openPopup();
        });

        function getRiskLevel(ttf) {
            if (ttf < 3) return { level: 'HØYRISIKO', class: 'risk-high' };
            if (ttf < 6) return { level: 'MEDIUMRISIKO', class: 'risk-medium' };
            return { level: 'LAVRISIKO', class: 'risk-low' };
        }

        async function fetchWeatherAndRisk() {
            const lat = document.getElementById('latitude').value;
            const lon = document.getElementById('longitude').value;
            const alt = document.getElementById('altitude').value;
            
            if (!lat || !lon) {
                alert('Vennligst velg en lokasjon på kartet');
                return;
            }
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('weatherDisplay').classList.remove('show');
            document.getElementById('fireriskDisplay').classList.remove('show');
            document.getElementById('errorResult').classList.remove('show');
            
            try {
                // Fetch latest weather and fire risk
                const weatherUrl = `/api/weather/latest?latitude=${lat}&longitude=${lon}${alt ? '&altitude=' + alt : ''}`;
                const weatherResponse = await fetch(weatherUrl);
                
                if (!weatherResponse.ok) {
                    const error = await weatherResponse.json();
                    throw new Error(error.detail || 'Feil ved henting av værdata');
                }
                
                const weatherData = await weatherResponse.json();
                const weather = weatherData.weather;
                
                document.getElementById('result-time').textContent = new Date(weather.timestamp).toLocaleString('no-NO');
                document.getElementById('result-temp').textContent = weather.temperature.toFixed(1) + '°C';
                document.getElementById('result-humidity').textContent = (weather.humidity * 100).toFixed(0) + '%';
                document.getElementById('result-wind').textContent = weather.wind_speed.toFixed(1) + ' m/s';
                
                document.getElementById('weatherDisplay').classList.add('show');
                
                // Fetch fire risk forecast
                const forecastUrl = `/api/forecast?latitude=${lat}&longitude=${lon}`;
                const forecastResponse = await fetch(forecastUrl);
                
                if (!forecastResponse.ok) {
                    const error = await forecastResponse.json();
                    throw new Error(error.detail || 'Feil ved beregning av brannrisiko');
                }
                
                const forecastData = await forecastResponse.json();
                
                if (forecastData.current_ttf !== null && forecastData.forecast && forecastData.forecast.length > 0) {
                    const ttf = forecastData.current_ttf;
                    const risk = getRiskLevel(ttf);
                    
                    document.getElementById('result-ttf').textContent = ttf.toFixed(2);
                    const riskLevelDiv = document.getElementById('result-risk-level');
                    riskLevelDiv.textContent = risk.level;
                    riskLevelDiv.className = 'risk-level ' + risk.class;
                    
                    document.getElementById('fireriskDisplay').classList.add('show');
                    
                    // Update forecast chart
                    updateForecastChart(forecastData.forecast);
                } else {
                    throw new Error('Ingen brannrisikodata tilgjengelig');
                }
                
            } catch (error) {
                const errorDiv = document.getElementById('errorResult');
                errorDiv.innerHTML = `<strong>Feil:</strong> ${error.message}`;
                errorDiv.classList.add('show');
            } finally {
                document.getElementById('loading').classList.remove('show');
            }
        }

        function updateForecastChart(forecast) {
            const ctx = document.getElementById('forecastChart').getContext('2d');
            
            const labels = forecast.slice(0, 24).map((f, i) => `+${i}h`);
            const data = forecast.slice(0, 24).map(f => f.ttf);
            
            if (forecastChart) {
                forecastChart.destroy();
            }
            
            forecastChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'TTF',
                        data: data,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: { font: { size: 12 } }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 10,
                            ticks: { stepSize: 2 }
                        }
                    }
                }
            });
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
    Returns current fire risk based on actual weather + 7-day forecast trend.
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
        # Fetch current weather to get baseline fire risk
        logger.info(f"Fetching current weather for lat={lat}, lon={lon}")
        current_weather = await fetch_met_latest(lat, lon, altitude=None)
        
        # Fetch 7 days of weather data for fire risk trend computation
        # (Fire risk model simulates wood moisture changes over time)
        logger.info(f"Fetching 7-day forecast for lat={lat}, lon={lon} for fire risk trend")
        weather_points = await fetch_met_forecast(lat, lon, altitude=None, days=7)
        
        if not weather_points or len(weather_points) < 2:
            raise ValueError(f"Insufficient weather data: got {len(weather_points)} points, need at least 2 for fire risk computation")
        
        logger.info(f"Computing fire risk forecast with {len(weather_points)} weather data points for lat={lat}, lon={lon}")
        
        # Convert to WeatherData format
        from frcm.datamodel.utils import list_to_wdps
        data_points = list_to_wdps(weather_points)
        weather_obj = WeatherData(data=data_points)
        
        # Calculate fire risk trend
        fire_risk = compute(weather_obj)
        
        # Create current fire risk point based on actual current conditions
        # We compute a single-point fire risk using just the current weather
        current_point = {
            "timestamp": current_weather["timestamp"],
            "temperature": current_weather["temperature"],
            "humidity": current_weather["humidity"],
            "wind_speed": current_weather["wind_speed"]
        }
        current_data_point = WeatherDataPoint(
            timestamp=current_weather["timestamp"],
            temperature=current_weather["temperature"],
            humidity=current_weather["humidity"],
            wind_speed=current_weather["wind_speed"]
        )
        # Create a 48-hour window around current time using forecast data
        # to give the model enough data for realistic wood moisture computation
        current_and_future = [current_point] + weather_points[:48]  # ~2 days including current
        current_data_points = list_to_wdps(current_and_future)
        current_weather_obj = WeatherData(data=current_data_points)
        current_fire_risk = compute(current_weather_obj)
        
        # Extract current TTF (first value computed from current conditions)
        current_ttf = current_fire_risk.firerisks[0].ttf if current_fire_risk.firerisks else None
        
        logger.info(f"Successfully computed fire risk for {location or f'({lat}, {lon})'}: current_ttf={current_ttf}, forecast_points={len(fire_risk.firerisks)}")
        
        return {
            "location": location or f"({lat}, {lon})",
            "latitude": lat,
            "longitude": lon,
            "current_ttf": current_ttf,
            "current_weather": current_point,
            "data_points": len(weather_points),
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
