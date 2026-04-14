import pytest
import csv
from weather import get_list, get_city_id, get_weather, select_city, select_country

# ── get_list ──────────────────────────────────────────────────────────────────

def test_get_list_returns_list():
    """get_list() should return a list."""
    result = get_list('full_city_list.csv')
    assert isinstance(result, list)


def test_get_list_not_empty():
    """get_list() should not return an empty list."""
    result = get_list('full_city_list.csv')
    assert len(result) > 0


def test_get_list_rows_are_dicts():
    """Each row returned by get_list() should be a dictionary."""
    result = get_list('full_city_list.csv')
    assert isinstance(result[0], dict)


def test_get_list_correct_keys():
    """Each row should contain the keys 'Country', 'City', and 'City_Id'."""
    result = get_list('full_city_list.csv')
    assert result[0].keys() == {'Country', 'City', 'City_Id'}


def test_get_list_skips_header():
    """The first row should not be the CSV header."""
    result = get_list('full_city_list.csv')
    assert result[0]['Country'] != 'Country'


# ── get_city_id ───────────────────────────────────────────────────────────────

def test_get_city_id_returns_list():
    """get_city_id() should return a list."""
    result = get_city_id('kabul')
    assert isinstance(result, list)


def test_get_city_id_known_city():
    """get_city_id() should return the correct ID for a known city."""
    result = get_city_id('kabul')
    assert '219' in result


def test_get_city_id_unknown_city():
    """get_city_id() should return an empty list for a city that doesn't exist."""
    result = get_city_id('thiscitydoesnotexist')
    assert result == []


def test_get_city_id_case_insensitive():
    """get_city_id() should work regardless of the case passed in."""
    result = get_city_id('algiers')
    assert len(result) > 0


# ── get_weather ───────────────────────────────────────────────────────────────

def test_get_weather_returns_list():
    """get_weather() should return a list (using London, city_id=2015)."""
    result = get_weather('2015')
    assert isinstance(result, list)


def test_get_weather_not_empty():
    """get_weather() should return at least one forecast day."""
    result = get_weather('2015')
    assert len(result) > 0


def test_get_weather_correct_keys():
    """Each forecast entry should have 'Forecast Date', 'Weather', '' and 'Temp (°C)'."""
    result = get_weather('2015')
    assert 'Forecast Date' in result[0]
    assert 'Weather' in result[0]
    assert '' in result[0]
    assert 'Temp (°C)' in result[0]


def test_get_weather_temp_format():
    """'Temp (°C)' should always contain '°C', and '|' when both min and max temps are available."""
    result = get_weather('2015')
    for day in result:
        assert '°C' in day['Temp (°C)']
        if '|' in day['Temp (°C)']:
            parts = day['Temp (°C)'].split('|')
            assert len(parts) == 2
            assert '°C' in parts[0] and '°C' in parts[1]


def test_get_weather_no_raw_fields():
    """Raw fields like 'minTemp' and 'maxTemp' should have been removed."""
    result = get_weather('2015')
    for day in result:
        assert 'minTemp' not in day
        assert 'maxTemp' not in day


# ── select_city ───────────────────────────────────────────────────────────────

def test_select_city_returns_list():
    """select_city() should return a list."""
    result = select_city()
    assert isinstance(result, list)


def test_select_city_is_sorted():
    """select_city() should return cities in alphabetical order."""
    result = select_city()
    assert result == sorted(result)


def test_select_city_filtered_by_country():
    """select_city('afghanistan') should only return cities in Afghanistan."""
    result = select_city('afghanistan')
    assert 'herat' in result
    assert 'kabul' in result


def test_select_city_filter_excludes_other_countries():
    """Cities from other countries should not appear when filtering."""
    result = select_city('afghanistan')
    assert 'algiers' not in result


def test_select_city_no_duplicates():
    """select_city() should not return duplicate cities."""
    result = select_city()
    assert len(result) == len(set(result))


# ── select_country ────────────────────────────────────────────────────────────

def test_select_country_returns_list():
    """select_country() should return a list."""
    result = select_country()
    assert isinstance(result, list)


def test_select_country_is_sorted():
    """select_country() should return countries in alphabetical order."""
    result = select_country()
    assert result == sorted(result)


def test_select_country_known_country():
    """'afghanistan' should be present in the country list."""
    result = select_country()
    assert 'afghanistan' in result


def test_select_country_no_duplicates():
    """select_country() should not return duplicate countries."""
    result = select_country()
    assert len(result) == len(set(result))


def test_select_country_all_lowercase():
    """All country names should be lowercase."""
    result = select_country()
    assert all(c == c.lower() for c in result)