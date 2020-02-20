#!/usr/bin/env python3
"""Tweet the air quality in Hong Kong"""

import os
import json
import requests
import tweepy

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
                         "no2": "NO₂",
                         "o3": "O₃",
                         "so2": "SO₂"}

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

class Twitter:
    """Wrapper for the Twitter API"""
    HK_PLACE_ID = "35fd5bacecc4c6e5"

    def __init__(self, api: tweepy.API) -> None:
        self.api = api

    # pylint: disable=invalid-name
    @staticmethod
    def _compose(aq: AirQuality) -> str:
        return "AQI: {}. The dominant pollutant is {}. (This is {}.)" \
            .format(aq.aqi, aq.dominant_pollutant(), aq.category)

    def _criteria(self, status: str) -> bool:
        try:
            return status != self.api.user_timeline(count=1).pop().text
        except tweepy.error.TweepError as exception:
            print("Criteria failed with API error")
            raise exception

    def update(self, aq: AirQuality) -> bool:
        """Send a tweet"""
        status = self._compose(aq)
        if self._criteria(status):
            try:
                print("[{}]: {}".format(aq.localtime, status))
                self.api.update_status(status=status, place_id=self.HK_PLACE_ID)
                return True
            except tweepy.error.TweepError as exception:
                print("Failed to update with API error")
                raise exception
        print("Status \"{}\" is a duplicate".format(status))
        return False

def main() -> None:
    """Entry point"""
    auth = tweepy.OAuthHandler(os.environ["API_KEY"], os.environ["API_SECRET"])
    auth.set_access_token(os.environ["ACCESS_TOKEN"],
                          os.environ["ACCESS_TOKEN_SECRET"])
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    # pylint: disable=invalid-name
    aq = AirQuality()
    twitter = Twitter(api)
    twitter.update(aq)

if __name__ == "__main__":
    main()
