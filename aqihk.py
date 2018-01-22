#!/usr/bin/env python3

import time
import requests
import tweepy
import aqicn
from credentials import api_key, api_secret, access_token, access_token_secret

AUTH = tweepy.OAuthHandler(api_key, api_secret)
AUTH.set_access_token(access_token, access_token_secret)
API = tweepy.API(AUTH, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

class AirQuality:

    def __init__(self):
        self._aqi_dict = self._aqi_data()
        self.aqi = int(self._aqi_dict["aqi"])
        self.dominant_pollutant = self._aqi_dict["dominentpol"]
        self.category = self._category()
        self.time = self._aqi_dict["time"]["v"]
        self.localtime = self._aqi_dict["time"]["s"] \
                         + self._aqi_dict["time"]["tz"]

    @staticmethod
    def _aqi_data():
        payload = {"token": aqicn.token}
        r = requests.get("https://api.waqi.info/feed/@3308/", params = payload)
        r = r.json()
        assert r["status"] == "ok"
        return r["data"]

    def _category(self):
        if self.aqi <= 50:
            return "good"
        elif self.aqi <= 100:
            return "moderate"
        elif self.aqi <= 150:
            return "unhealthy for sensitive groups"
        elif self.aqi <= 200:
            return "unhealthy"
        elif self.aqi <= 300:
            return "very unhealthy"
        elif self.aqi <= 500:
            return "hazardus"
        return "off the scale"

def compose(aq):
    pollutant_map = {"pm25": "PM2.5",
                     "pm10": "PM10",
                     "co": "CO",
                     "no2": "NO2",
                     "o3": "O3",
                     "so2": "SO2"}
    dominant_pollutant = pollutant_map.get(aq.dominant_pollutant)

    composition = "AQI: {}. The dominant pollutant is {}. (This is {}.)" \
                  .format(aq.aqi, dominant_pollutant, aq.category)
    return composition

def criteria(status):
    return status != API.user_timeline(count = 1).pop().text

def update(aq):
    status = compose(aq)
    if criteria(status):
        try:
            print("[{}]: {}".format(aq.localtime, status))
            API.update_status(status = status, place_id = "35fd5bacecc4c6e5")
        except tweepy.error.TweepError as e:
            print(e)

def main():
    previous_aq = None

    while True:
        aq = AirQuality()
        if previous_aq is None:
            update(aq)
            previous_aq = aq
        elif aq.time > previous_aq.time:
            update(aq)
            previous_aq = aq
        else:
            time.sleep(240)

if __name__ == "__main__":
    main()

