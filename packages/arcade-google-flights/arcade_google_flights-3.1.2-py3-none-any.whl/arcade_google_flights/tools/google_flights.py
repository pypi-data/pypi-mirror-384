from typing import Annotated, Any

from arcade_tdk import ToolContext, tool

from arcade_google_flights.enums import (
    GoogleFlightsMaxStops,
    GoogleFlightsSortBy,
    GoogleFlightsTravelClass,
)
from arcade_google_flights.utils import call_serpapi, parse_flight_results, prepare_params


@tool(requires_secrets=["SERP_API_KEY"])
async def search_one_way_flights(
    context: ToolContext,
    departure_airport_code: Annotated[
        str, "The departure airport code. An uppercase 3-letter code"
    ],
    arrival_airport_code: Annotated[str, "The arrival airport code. An uppercase 3-letter code"],
    outbound_date: Annotated[str, "Flight departure date in YYYY-MM-DD format"],
    currency_code: Annotated[
        str | None, "Currency of the returned prices. Defaults to 'USD'"
    ] = "USD",
    travel_class: Annotated[
        GoogleFlightsTravelClass,
        "Travel class of the flight. Defaults to 'ECONOMY'",
    ] = GoogleFlightsTravelClass.ECONOMY,
    num_adults: Annotated[int | None, "Number of adult passengers. Defaults to 1"] = 1,
    num_children: Annotated[int | None, "Number of child passengers. Defaults to 0"] = 0,
    max_stops: Annotated[
        GoogleFlightsMaxStops,
        "Maximum number of stops (layovers) for the flight. Defaults to any number of stops",
    ] = GoogleFlightsMaxStops.ANY,
    sort_by: Annotated[
        GoogleFlightsSortBy,
        "The sorting order of the results. Defaults to TOP_FLIGHTS.",
    ] = GoogleFlightsSortBy.TOP_FLIGHTS,
) -> Annotated[dict[str, Any], "Flight search results from the Google Flights API"]:
    """Retrieve flight search results for a one-way flight using Google Flights"""
    params = prepare_params(
        "google_flights",
        departure_id=departure_airport_code,
        arrival_id=arrival_airport_code,
        outbound_date=outbound_date,
        currency=currency_code,
        travel_class=travel_class.to_api_value(),
        adults=num_adults,
        children=num_children,
        stops=max_stops.to_api_value(),
        sort_by=sort_by.to_api_value(),
        type=2,  # indicates one-way
        deep_search=True,  # Same search depth as the Google Flights page in the browser
    )

    # Execute the request
    results = call_serpapi(context, params)

    # Parse the results
    flights = parse_flight_results(results)

    return flights
