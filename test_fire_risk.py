import asyncio
from frcm.datacontroller import fetch_met_forecast
from frcm.datamodel.utils import list_to_wdps
from frcm.datamodel.model import WeatherData
from frcm.fireriskmodel.compute import compute

async def test():
    # Test with Bergen
    weather_data = await fetch_met_forecast(60.3913, 5.3221, days=7)
    print(f'Weather points: {len(weather_data)}')
    print(f'First 3 points:')
    for i, p in enumerate(weather_data[:3]):
        print(f'  {i}: temp={p["temperature"]:.1f}°C, humidity={p["humidity"]:.3f}, wind={p["wind_speed"]:.1f}')
    
    # Convert and compute fire risk
    data_points = list_to_wdps(weather_data)
    weather_obj = WeatherData(data=data_points)
    fire_risk = compute(weather_obj)
    
    print(f'\nFire risk output:')
    print(f'  Total TTF values: {len(fire_risk.firerisks)}')
    print(f'  First 5 TTF values:')
    for i, risk in enumerate(fire_risk.firerisks[:5]):
        print(f'    {i}: {risk.ttf:.2f}')
    print(f'  Last 5 TTF values:')
    for i, risk in enumerate(fire_risk.firerisks[-5:]):
        print(f'    {len(fire_risk.firerisks)-5+i}: {risk.ttf:.2f}')

asyncio.run(test())
