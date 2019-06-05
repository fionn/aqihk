#!/usr/bin/env python3
"""Tweet the air quality in Hong Kong"""

import os
import time
import json
import requests
import tweepy

AUTH = tweepy.OAuthHandler(os.environ["API_KEY"], os.environ["API_SECRET"])
AUTH.set_access_token(os.environ["ACCESS_TOKEN"],
                      os.environ["ACCESS_TOKEN_SECRET"])
API = tweepy.API(AUTH, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# pylint: disable=too-few-public-methods
class AirQuality:
    """AQICN interface"""

    def __init__(self) -> None:
        self._aqi_dict = self._aqi_data()
        self.aqi = int(self._aqi_dict["aqi"])
        self.category = self._category()
        self.time = self._aqi_dict["time"]["v"]
        self.localtime = self._aqi_dict["time"]["s"] \
                         + self._aqi_dict["time"]["tz"]

    def dominant_pollutant(self) -> str:
        """Gets the dominant pollutant"""
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
        payload = {"token": os.environ["AQICN_TOKEN"]}
        while True:
            try:
                response = requests.get(endpoint, params=payload)
                response.raise_for_status()
                response_dict = response.json()
                if response_dict["status"] != "ok":
                    raise requests.HTTPError(response_dict["status"])
                return response_dict["data"]
            except requests.exceptions.ConnectionError as exception:
                exception_handler(exception)
            except json.JSONDecodeError:
                print("Bad API data: {}".format(response.text), flush=True)
                raise

    # pylint: disable=too-many-return-statements
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

# pylint: disable=invalid-name
def compose(aq: AirQuality) -> str:
    """Write the tweet"""
    return "AQI: {}. The dominant pollutant is {}. (This is {}.)" \
           .format(aq.aqi, aq.dominant_pollutant(), aq.category)

def criteria(status: str) -> bool:
    """Check if status can be sent"""
    try:
        return status != API.user_timeline(count=1).pop().text
    except tweepy.error.TweepError as exception:
        exception_handler(exception)
        return False

def update(aq: AirQuality) -> None:
    """Send a tweet"""
    status = compose(aq)
    if criteria(status):
        try:
            print("[{}]: {}".format(aq.localtime, status))
            #API.update_status(status=status, place_id="35fd5bacecc4c6e5")
        except tweepy.error.TweepError as exception:
            print("Failed to update, handling exception")
            exception_handler(exception)
    else:
        print("Status \"{}\" is a duplicate".format(status))

def exception_handler(exception: Exception) -> None:
    """API is super fragile, so just handle it here"""
    print(exception)
    t_sleep = 15 * 60
    print("Sleeping for {} seconds".format(t_sleep))
    time.sleep(t_sleep)
    print("Waking up")

def main() -> None:
    """Entry point"""
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
                print("Current status is newer; updating...")
                update(aq)
                previous_aq = aq
                time.sleep(sleep_time)
            else:
                print("Update failed even though we got a new status.")
                print("Previous status: [{}] {}".format(previous_aq.time,
                                                        compose(previous_aq)))
                print("New status: [{}] {}".format(aq.time, compose(aq)))
                print("Sleeping for {} seconds...".format(sleep_time * 10))
                time.sleep(sleep_time * 10)
        except json.JSONDecodeError as exception:
            exception_handler(exception)

if __name__ == "__main__":
    main()
