import requests
import datetime
from frcm.datamodel.model import WeatherData, WeatherDataPoint


def hent_weatherdata_fra_met(lat: float, lon: float) -> WeatherData:
    url = (
        "https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={lat}&lon={lon}"
    )

    headers = {
        "User-Agent": "FireguardProsjekt/1.0 begry6463@hvl.no"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Feil ved henting av data: {response.status_code}")

    data = response.json()
    timeseries = data["properties"]["timeseries"]

    datapunkter = []

    for entry in timeseries:
        # MET bruker "Z" for UTC → må konverteres til +00:00 for Python
        timestamp = datetime.datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        details = entry["data"]["instant"]["details"]

        dp = WeatherDataPoint(
            timestamp=timestamp,
            temperature=details["air_temperature"],
            humidity=details["relative_humidity"],
            wind_speed=details["wind_speed"]
        )

        datapunkter.append(dp)

    return WeatherData(data=datapunkter)


# Eksempelbruk
if __name__ == "__main__":
    lat = 60.3691
    lon = 5.3495

    wd = hent_weatherdata_fra_met(lat, lon)
    print(wd)