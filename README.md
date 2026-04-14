# Weather Forecast
#### Video Demo: <URL HERE>

## Description

Weather Forecast is an interactive command-line application that retrieves official weather forecasts from the **World Meteorological Organization (WMO)**. The WMO is a specialized agency of the United Nations responsible for promoting international cooperation on atmospheric science, climatology, hydrology and geophysics. The WMO is made up of 193 countries and territories, and facilitates the exchange of data and information between the respective meteorological institutions of its members. The WMO also provides a public API that is free to use and offers well-structured, stable data.

## How to use

When launched the program will prompt the user to type a country name. Partial input is accepted — e.g. if the user types "ital" and only Italy matches, it is selected automatically. If multiple countries match, the program will display the matches and ask the user to be more specific. Once a country is confirmed, the program lists all available cities for that country and asks the user to choose one using the same fuzzy-matching logic. The forecast is then fetched from the WMO API and printed as a formatted table showing the upcoming days.

Each row in the forecast table contains:
- **Forecast Date** — shown as "Today", "Tomorrow", or the weekday for future dates
- **Weather** — a short description of expected conditions (e.g. "Sunny", "Heavy Rain")
- **Emoji** — a visual icon matching the weather description
- **Temp (°C)** — the daily temperature range formatted as `min°C | max°C`

## Contents

- ```weather.py```

The main program. Contains all application logic: fetching and caching the city list, querying the WMO API, formatting the forecast table, and handling interactive country/city selection with fuzzy matching.

- ```test_weather.py```

Pytest test suite with 24 tests covering the core functions. Verifies return types, known values, edge cases, and correct output formatting. Tests for `get_weather()` require an internet connection; all others run offline.

-  ```full_city_list.csv```

Local copy of the WMO city list with three columns: `Country`, `City`, and `City_Id`. Used to look up city IDs without a network request on every run. Refresh with `python weather.py -u`.

- ```requirements.txt```

Lists the four third-party dependencies: `requests`, `tabulate`, `pyfiglet`, and `rich`.

## Design Choices

One deliberate choice was local caching of the city list. An alternative would have been to fetch it from the WMO on every run, which would guarantee freshness but add latency and require a network connection just to browse countries. Storing it locally with an explicit `-u` update flag strikes a better balance: the list rarely changes, so fetching it on demand is sensible.

Fuzzy matching for country and city names was chosen over requiring exact input because the WMO uses official UN names that users might not know — "Iran (Islamic Republic of)" rather than "Iran", for example. The `NAME_OVERRIDES` dictionary normalizes the most common cases, and substring matching handles the rest, making the program forgiving without sacrificing correctness.

## Prerequisites

Supported python: ![Python version](https://img.shields.io/badge/python-3.8%2B-blue)

First of all ensure to have the right python version installed.

This project uses third-party libraries: see the
[requirements](requirements.txt) for more information.

## How to Run

> ⚠️ The program requires an internet connection. Be sure to be connected.


Install the dependencies:
```bash
pip install -r requirements.txt
```

Run the program:
```bash
python weather.py
```

To update the full city list:
```bash
python weather.py -u
```

Run the tests:
```bash
pytest test_weather.py
```

For a full example on how to use this program, please refer to [demo](URL HERE).

## Author
* <img src="https://avatars.githubusercontent.com/u/135356553?v=4" width="25px;"/> **Lorenzo Palazzi** [git](https://github.com/palazzilorenzo)
