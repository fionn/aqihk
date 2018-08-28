#!/usr/bin/env python3

import time
import json
import requests
import tweepy
import aqicn
from credentials import api_key, api_secret, access_token, access_token_secret

AUTH = tweepy.OAuthHandler(api_key, api_secret)
AUTH.set_access_token(access_token, access_token_secret)
API = tweepy.API(AUTH, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

class AirQuality:

    def __init__(self) -> None:
        self._aqi_dict = self._aqi_data()
        self.aqi = int(self._aqi_dict["aqi"])
        self.category = self._category()
        self.time = self._aqi_dict["time"]["v"]
        self.localtime = self._aqi_dict["time"]["s"] \
                         + self._aqi_dict["time"]["tz"]

    def dominant_pollutant(self) -> str:
        pollutant_map = {"pm25": "PM2.5",
                         "pm10": "PM10",
                         "co": "CO",
                         "no2": "NO2",
                         "o3": "O3",
                         "so2": "SO2"}

        density = 0
        dominant_pollutant = None
        iaqi = self._aqi_dict["iaqi"]
        for pollutant in pollutant_map:
            aqi = iaqi[pollutant]["v"]
            if aqi > density:
                density = aqi
                dominant_pollutant = pollutant

        if not dominant_pollutant:
            raise RuntimeError("No dominant pollutant")

        return pollutant_map[dominant_pollutant]

    @staticmethod
    def _aqi_data() -> dict:
        endpoint = "https://api.waqi.info/feed/@3308/"
        payload = {"token": aqicn.token}
        while True:
            try:
                r = requests.get(endpoint, params=payload)
                r.raise_for_status()
                response = r.json()
                if response["status"] != "ok":
                    raise requests.HTTPError(response["status"])
                return response["data"]
            except requests.exceptions.ConnectionError as e:
                exception_handler(e)
            except json.JSONDecodeError:
                print("Bad API data: {}".format(r.text), flush=True)
                raise

    def _category(self) -> str:
        if self.aqi <= 50:
            return "good"
        if self.aqi <= 100:
            return "moderate"
        if self.aqi <= 150:
            return "unhealthy for sensitive groups"
        if self.aqi <= 200:
            return "unhealthy"
        if self.aqi <= 300:
            return "very unhealthy"
        if self.aqi <= 500:
            return "hazardous"
        return "off the scale"

def compose(aq: AirQuality) -> str:
    composition = "AQI: {}. The dominant pollutant is {}. (This is {}.)" \
                  .format(aq.aqi, aq.dominant_pollutant(), aq.category)
    return composition

def criteria(status: str) -> bool:
    try:
        return status != API.user_timeline(count=1).pop().text
    except tweepy.error.TweepError as e:
        exception_handler(e)
        return False

def update(aq: AirQuality) -> None:
    status = compose(aq)
    if criteria(status):
        try:
            print("[{}]: {}".format(aq.localtime, status))
            API.update_status(status=status, place_id="35fd5bacecc4c6e5")
        except tweepy.error.TweepError as e:
            exception_handler(e)
    else:
        print("Status \"{}\" is a duplicate".format(status))

def exception_handler(e: Exception) -> None:
    print(e)
    t = 15 * 60
    print("Sleeping for {} seconds".format(t))
    time.sleep(t)
    print("Waking up")

def main() -> None:
    previous_aq = None
    sleep_time = 240

    while True:
        try:
            aq = AirQuality()
            if previous_aq is None:
                update(aq)
                previous_aq = aq
                time.sleep(sleep_time)
            elif aq.time > previous_aq.time:
                update(aq)
                previous_aq = aq
                time.sleep(sleep_time)
            else:
                print("Just sleeping")
                time.sleep(sleep_time)
        except json.JSONDecodeError as e:
            exception_handler(e)

if __name__ == "__main__":
    main()

