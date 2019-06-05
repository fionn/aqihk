# Air Quality in Hong Kong

A Twitter bot (running at [@aqihk](https://twitter.com/aqihk)) that tweets the current air quality index in Hong Kong in approximately real-time.

## Deployment

Provide environment variables for WAQI API `TOKEN` and Twitter API credentials (see [twitterauthenticator](https://github.com/fionn/twitterauthenticator)).
Generate a virtual environment with `make venv`. This will also pull in the latest dependencies from PyPI.
