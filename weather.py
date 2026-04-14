import requests
import sys
import csv
import argparse
from tabulate import tabulate
from pyfiglet import Figlet
import datetime
import cmd
from rich.console import Console

# Lists of weather conditions mapped to emojis
thunderstorm = ['Thunderstorms', 'Thundershowers', 'Storm', 'Lightning']
snow = ['Hail', 'Snow Showers', 'Flurries', 'Snow', 'Heavy Snow', 'Snowfall', 'Light Snow', 'Sleet', 'Freezing Rain']
snowstorm = ['Blowing Snow', 'Blizzard', 'Snowdrift', 'Snowstorm']
rain = ['Showers', 'Heavy Showers', 'Rainshower', 'Light Showers', 'Rain', 'Drizzle', 'Light Rain']
fog = ['Fog', 'Mist']
clearing = ['Sunny Intervals', 'No Rain', 'Clearing']
sun_cloud = ['Sunny Periods', 'Partly Cloudy', 'Partly Bright', 'Mild']
sun_rain = ['Occasional Showers', 'Scattered Showers', 'Isolated Showers']
cloudy = ['Cloudy', 'Mostly Cloudy', 'Overcast']
sunny = ['Bright', 'Sunny', 'Fair', 'Fine', 'Clear']
wind = ['Windy', 'Squall', 'Stormy', 'Gale']
humid = ['Wet', 'Humid']

# Dictionary mapping each weather condition to its emoji
WEATHER_EMOJIS = {
    **{w: '🌫️' for w in fog},
    **{w: '⛈️' for w in thunderstorm},
    **{w: '🌨️' for w in snow},
    **{w: '❄️' for w in snowstorm},
    **{w: '🌧️' for w in rain},
    **{w: '🌥️' for w in clearing},
    **{w: '🌤️' for w in sun_cloud},
    **{w: '🌦️' for w in sun_rain},
    **{w: '☁️' for w in cloudy},
    **{w: '☀️' for w in sunny},
    **{w: '🌬️' for w in wind},
    **{w: '💧' for w in humid},
}

# Fields to remove from each forecast day returned by the WMO API
FIELDS_TO_REMOVE = ['minTemp', 'maxTemp', 'wxdesc', 'minTempF', 'maxTempF', 'weatherIcon']

# Encoding corruption fixes applied to the raw downloaded text
CSV_REPLACEMENTS = {
    'TÃ¼rkiye': 'Türkiye',
    'CuraÃ§ao': 'Curaçao',
    'CÃ´te': 'Côte',
}

# Country name normalisations applied after CSV parsing (case-insensitive) in get_list().
NAME_OVERRIDES = {
    'gambia (the)': 'Gambia',
    'iran (islamic republic of)': 'Iran',
    'libya (state of)': 'Libya',
    'netherlands (kingdom of the)': 'Netherlands',
    'republic of korea': 'Korea',
    'republic of moldova': 'Moldova',
    'russian federation': 'Russia',
}

path = 'full_city_list.csv'

# Module-level cache so the CSV is read from disk only once per session
_city_list = None

console = Console()

def main():
    args = arg_parse()
    if args.update:
        update_full_city_list()
    else:
        title()
        console.print(
            "Type a country to get started "
            "(press [white on yellow]Enter[/white on yellow] to see the full list)"
        )
        try:
            s = input("-->").lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nGoodbye!")
        if location := check_country(s):
            print('─' * (len(location[0])+14))
            console.print(f"[white on green] ✓ [/white on green] {location[0].title()} selected")
            print('─' * (len(location[0])+14))
            cities = [city.title() for city in location[1]]
            print(f"\nAvailable cities for {location[0].title()}:\n")
            cli = cmd.Cmd()
            cli.columnize(cities, displaywidth=40)
            city = check_city(location[1])
            print('─' * (len(city)+14))
            console.print(f"[white on green] ✓ [/white on green] {city.title()} selected")
            print('─' * (len(city)+14))
            city_id = get_city_id(city)
            weather = get_weather(*city_id)
            if not weather:
                print('\nWeather forecast information is not available at this moment, try later.\n')
            else:
                print('\n', tabulate(weather, headers="keys", tablefmt="simple", colalign=("left", "left", "left", "right")), '\n')


def check_city(cities):
    '''
    Asks the user to type a city name and checks if it is valid.
 
    If the input matches exactly one city that starts with what was typed,
    that city is returned automatically. If more than one city matches,
    they are shown and the user is asked to be more specific.
    Keeps asking until a valid city is entered.

    :param cities: list of valid city names for the selected country
    :type cities: list
    :return: the matched city name
    :rtype: str
    '''
    while True:
        try:
            c = input("\nType one of the cities above\n--> ").lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nGoodbye!")
        if c in cities:
            return c
        if len(c) == 1:
            matches = [s for s in cities if s.startswith(c)]
        else:
            matches = [city for city in cities if c in city]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print('─' * 51)
            console.print("[white on orange3] ! [/white on orange3] Multiple cities match, please be more specific:")
            print('─' * 51)
            cli = cmd.Cmd()
            cli.columnize([m.title() for m in matches], displaywidth=40)
        else:
            print('─' * 37)
            console.print("[white on red] X [/white on red] City not found. Please try again.")
            print('─' * 37)


def check_country(s=None):
    '''
    Asks the user to type a country name and checks if it is valid.
 
    If the input matches exactly one country that starts with what was typed,
    that country is returned automatically. If more than one country matches,
    they are shown and the user is asked to be more specific. If nothing
    matches, countries starting with the same letter are suggested as hints.
    Keeps asking until a valid country is entered.

    :param s: country name typed by the user
    :type s: str
    :return: tuple of (country_name, list_of_cities) if valid
    :rtype: tuple
    '''
    list_of_countries = select_country()
    if not s:
        countries = [country.title() for country in list_of_countries]
        cli = cmd.Cmd()
        cli.columnize(countries, displaywidth=32)
        try:
            s = input("\nType one of the countries above\n-->").lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nGoodbye!")
        return check_country(s)
    elif s in list_of_countries:
        return (s, select_city(s))
    else:
        if len(s) == 1:
            matches = [c for c in list_of_countries if c.startswith(s)]
        else:
            matches = [c for c in list_of_countries if c.startswith(s) or s in c]
        if len(matches) == 1:
            return (matches[0], select_city(matches[0]))
        elif len(matches) > 1:
            print('─' * 53)
            console.print("[white on orange3] ! [/white on orange3] Multiple countries match, please be more specific:\n")
            cli = cmd.Cmd()
            cli.columnize([m.title() for m in matches], displaywidth=40)
            try:
                s = input("\nType one of the countries above\n--> ").lower()
            except (EOFError, KeyboardInterrupt):
                sys.exit("\nGoodbye!")
        else:
            suggestions = [c.title() for c in list_of_countries if c[0] == s[0].lower()]
            if suggestions:
                print('─' * 52)
                console.print("[white on red] X [/white on red] Country not found, maybe you meant one of these:\n")
                cli = cmd.Cmd()
                cli.columnize(suggestions, displaywidth=40)
                try:
                    s = input("\nType one of the countries above\n--> ").lower()
                except (EOFError, KeyboardInterrupt):
                    sys.exit("\nGoodbye!")
            else:
                print('─' * 75)
                console.print("[white on red] X [/white on red] Country not found. Try again or press [white on yellow] Enter [/white on yellow] to see the full list\n--> ", end='')
                try:
                    s = input().lower()
                except (EOFError, KeyboardInterrupt):
                    sys.exit("\nGoodbye!")
        return check_country(s)


def arg_parse():
    '''
    Defines and parses command-line arguments.

    :return: parsed arguments object
    :rtype: argparse.Namespace
    '''
    parser = argparse.ArgumentParser(
        prog="Weather Forecast",
        description="Get official weather forecasts from the WMO (World Meteorological Organization)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-u', "--update",
        help="Download the updated city list from the WMO website and save it as full_city_list.csv",
        action="store_true"
    )
    return parser.parse_args()


def update_full_city_list():
    '''
    Downloads the updated city list from the WMO website, applies encoding
    fixes and saves it locally as full_city_list.csv.
 
    :raise SystemExit: if the HTTP request fails
    '''
    city_list_url = 'https://worldweather.wmo.int/en/json/full_city_list.txt'
    try:
        city_list_csv = requests.get(city_list_url).text
    except requests.RequestException:
        sys.exit(
            "Error: could not download the city list from "
            "https://worldweather.wmo.int/en/json/full_city_list.txt — "
            "check your internet connection and try again."
        )
    city_list_csv = city_list_csv.replace(';', ',')
    city_list_csv = city_list_csv.replace('"', '')
    for old, new in CSV_REPLACEMENTS.items():
        city_list_csv = city_list_csv.replace(old, new)
    transformed_lines = []
    for line in city_list_csv.splitlines():
        if line.startswith('United States of America,'):
            # Raw format: United States of America,City, State,City_Id
            # Target format: State (USA),City,City_Id
            # Split on first comma to drop the country, last comma to isolate city_id
            without_country = line.split(',', 1)[1]           # "City, State,City_Id"
            city_id = without_country.rsplit(',', 1)[1].strip()  # "City_Id"
            city_state = without_country.rsplit(',', 1)[0]    # "City, State"
            if ',' in city_state:
                city, state = city_state.rsplit(',', 1)
                city = city.strip()
                state = state.strip()
            else:
                # Edge case: no state column (e.g. "Washington DC")
                city = city_state.strip()
                state = 'Washington DC'
            transformed_lines.append(f"{state} (USA),{city},{city_id}")
        else:
            transformed_lines.append(line)
    city_list_csv = '\n'.join(transformed_lines)
    with open("full_city_list.csv", "w") as file:
        file.write(city_list_csv)
    print("full_city_list.csv successfully updated.")


def title():
    '''
    Prints the program title in ASCII art using pyfiglet.
    '''
    f = Figlet(font='small', width=100)
    console.print(f.renderText('Weather Forecast'), style="bold green", markup=False, highlight=False)


def get_list(path):
    '''
    Reads full_city_list.csv and returns all rows as a list of dictionaries,
    skipping the header and the last empty row. Applies country name fixes
    from NAME_OVERRIDES. The result is cached so the file is only read once per session.

    :return: list of dicts with keys 'Country', 'City', 'City_Id'
    :rtype: list
    '''
    global _city_list
    if _city_list is None:
        rows = []
        with open(path, 'r') as file:
            reader = csv.DictReader(file, fieldnames=['Country', 'City', 'City_Id'])
            for row in reader:
                row['Country'] = NAME_OVERRIDES.get(row['Country'].lower(), row['Country'])
                rows.append(row)
        _city_list = rows[1:-1]
    return _city_list


def get_city_id(c):
    '''
    Looks up the numeric City ID for the given city name in full_city_list.csv.

    :param c: city name to search for (case-insensitive)
    :type c: str
    :return: list of City ID strings matching the city name
    :rtype: list
    '''
    city_list = get_list(path)
    return [row["City_Id"] for row in city_list if row["City"].lower() == c]


def get_weather(city_id):
    '''
    Fetches the weather forecast for a city from the WMO JSON API and returns
    it as a list of dictionaries, one per forecast day. Formats dates, adds
    weather emojis, merges min/max temperatures and removes unused fields.

    :param city_id: numeric ID of the city
    :type city_id: str
    :return: list of dicts with keys 'Forecast Date', 'Weather', '', 'Temp (°C)'
    :rtype: list
    :raise SystemExit: if the HTTP request fails
    '''
    URL = f'https://worldweather.wmo.int/en/json/{city_id}_en.json'
    try:
        response = requests.get(URL)
        forecast_days = response.json()['city']['forecast']['forecastDay']
    except requests.RequestException:
        console.print(f"[white on red]Error[/white on red] Could not reach {URL}\nThe page you are looking for might have been removed, had its name changed or is temporarily unavailable.\n\n [white on yellow]Options:[/white on yellow]\n 1. Check your internet connection and try again.\n 2. Type the URL in a browser to see further informations.\n")
        sys.exit()
    except (KeyError, ValueError):
        return []

    today = datetime.date.today()
    weather_info = []

    for info in forecast_days:
        date = datetime.date.fromisoformat(info['forecastDate'])
        delta = (date - today).days
        if delta == 0:
            info['forecastDate'] = today.strftime('%-d %b') + ' (Today)'
        elif delta == 1:
            info['forecastDate'] = date.strftime('%-d %b') + ' (Tomorrow)'
        else:
            info['forecastDate'] = date.strftime('%-d %b (%a)')

        info['Forecast Date'] = info.pop('forecastDate')
        info['Weather'] = info.pop('weather')
        info[''] = WEATHER_EMOJIS.get(info['Weather'], '🌡️')

        if info['minTemp']:
            info['Temp (°C)'] = f"{info['minTemp']}°C | {info['maxTemp']}°C"
        else:
            info['Temp (°C)'] = f"{info['maxTemp']}°C"
        for key in FIELDS_TO_REMOVE:
            info.pop(key, None)

        weather_info.append(info)

    return weather_info


def select_city(country=None):
    '''
    Returns a sorted list of cities, optionally filtered by country.

    :param country: country name to filter by (case-insensitive), or None for all cities
    :type country: str or None
    :return: sorted list of city names
    :rtype: list
    '''
    my_list = get_list(path)
    if country is None:
        return sorted({line['City'] for line in my_list})
    return sorted({line['City'].lower() for line in my_list if line['Country'].lower() == country})


def select_country():
    '''
    Returns a sorted list of all unique country names from full_city_list.csv.

    :return: sorted list of country names in lowercase
    :rtype: list
    '''
    my_list = get_list(path)
    return sorted({line['Country'].lower() for line in my_list})


if __name__ == '__main__':
    main()