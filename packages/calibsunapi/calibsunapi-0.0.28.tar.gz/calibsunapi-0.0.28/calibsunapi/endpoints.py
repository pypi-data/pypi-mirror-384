import os

BASE = os.environ.get("URL_API_CALIBSUN", "https://api.calibsun.com")
API = "/api/v2"
OPEN = "/open"
PUBLIC = "/public"


class EndpointRoutes:
    TOKEN = BASE + API + OPEN + "/token"
    LISTPLANT = BASE + API + PUBLIC + "/listplant"
    UPLOAD = BASE + API + PUBLIC + "/uploadmeasurements/{site_id}/{format}"
    LATESTFORECASTDEMO = BASE + API + PUBLIC + "/latestforecastdemo/{target}"
    LATESTFORECASTDEMO_PROBA = BASE + API + PUBLIC + "/latestforecastdemo/probabilistic/{target}"
    LATESTFORECASTDEMO_DET = BASE + API + PUBLIC + "/latestforecastdemo/deterministic{target}"
    LATESTFORECAST = BASE + API + PUBLIC + "/latestforecast/{site_id}/{target}"
    LATESTFORECAST_PROBA = BASE + API + PUBLIC + "/latestforecast/probabilistic/{site_id}/{target}"
    LATESTFORECAST_DET = BASE + API + PUBLIC + "/latestforecast/deterministic{site_id}/{target}"
    FIXEDTIMEFORECAST = BASE + API + PUBLIC + "/fixedtimeforecast/{time}/{site_id}/{target}"
    FIXEDTIMEFORECAST_PROBA = BASE + API + PUBLIC + "/fixedtimeforecast/probabilistic/{time}/{site_id}/{target}"
    FIXEDTIMEFORECAST_DET = BASE + API + PUBLIC + "/fixedtimeforecast/deterministic/{time}/{site_id}/{target}"
    HISTORICAL_FORECAST = BASE + API + PUBLIC + "/forecast/{datetime}/{siteid}/{target}"
    HISTORICAL_FORECAST_PROBA = BASE + API + PUBLIC + "/forecast/{datetime}/probabilistic/{siteid}/{target}"
    HISTORICAL_FORECAST_DET = BASE + API + PUBLIC + "/forecast/{datetime}/deterministic/{siteid}/{target}"
    FORECASTAVAILABILITY = BASE + API + PUBLIC + "/forecastavailability/{site_id}/{target}"
