from datetime import datetime
import requests
from time import sleep
import urllib.parse
from .loading import Loading

url = "https://api.scryfall.com"
headers = {"User-Agent": "scry-thrly/0.1", "Accept": "*/*"}
TIMEOUT = (6.05, 20)

# NOTE: scryfall returns an 'object : card/list` which could be used to detemine how to display/add single/lists of cards

#################
# Return a random card (optional search parameters)


def get_random_card(query: str) -> list:
    clean_query = urllib.parse.quote(query)
    endpoint = "/cards/random/?q="

    try:

        res = requests.get(
            url + endpoint + clean_query, headers=headers, timeout=TIMEOUT
        )
        res.raise_for_status()

        card = res.json()

        warnings = card.get("warnings")
        if warnings:
            print(f"WARNING [RANDOM REQ]: {warnings}")

        if res.status_code == 200:
            print(
                # prints name in bold, type in italics
                f"Drew card: \033[1m{card['name']}\033[0m : \x1b[3m{card['type_line']}\x1b[0m from {card['set_name']} {card['color_identity']}"
            )
            print(f"{card['type_line']}")
            return [card]
        else:
            print("Something may have gone wrong... Status Code: ", res.status_code)
            return []
    except requests.exceptions.RequestException as err:
        print("ERROR: ", err)
        return []


#################
# Return list of cards based on search query


def get_card_list(query: str) -> list:

    clean_query = urllib.parse.quote(query)
    endpoint = "/cards/search?q="

    sleep(0.1)  # just in case we ever call this in a loop

    try:
        # loading animation
        loading = Loading().start()

        req_url = url + endpoint + clean_query
        # print(f"Requesting from: {req_url}")
        res = requests.get(req_url, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()

        page_one = res.json()
        # print(f"Search returned {page_one.get("total_cards", 0)} cards.")

        show_warnings(page_one)

        # If there are additional pages (has_more) keep requesting from the "next_page" url
        # Add subsequent results ("data") values into the card list

        is_paginated = page_one.get("has_more")
        next_page = page_one.get("next_page")

        card_list = page_one.get("data")

        while is_paginated:
            try:
                sleep(0.11)  # just in case we ever call this in a loop

                additional_res = requests.get(
                    next_page, headers=headers, timeout=TIMEOUT
                )
                additional_res.raise_for_status()
                new_page_results = additional_res.json()

                show_warnings(new_page_results)

                # add new results page items into card_list
                for i in new_page_results.get("data"):
                    card_list.append(i)

                # set values for next page if required
                is_paginated = new_page_results.get("has_more")
                next_page = new_page_results.get("next_page")

            except requests.exceptions.RequestException as err:
                print("ERROR subsequent pages: ", err)

        loading.end()
        if res.status_code == 200:
            return card_list
        else:
            print("Something may have gone wrong... Status Code: ", res.status_code)
            return []
    except requests.exceptions.RequestException as err:
        print("ERROR: ", err)
        return []


def show_warnings(res):
    warnings = res.get("warnings")
    if warnings:
        print(f"WARNING [LIST REQ]: {warnings}")


######################
# Retreive List of Set Releases


def check_date_past(date_to_check) -> str:
    # check the release date against today's date to see if its past or future
    date_to_check = datetime.date(datetime.fromisoformat(date_to_check))
    current_date = datetime.date(datetime.today())
    if current_date >= date_to_check:
        return "Past"
    else:
        return "Future"


def is_current_release(date_A: datetime, date_B: datetime) -> str:
    if check_date_past(date_A) == "Future" and check_date_past(date_B) == "Past":
        return "*"
    else:
        return "-"


def find_current_release(setlist: list) -> dict:
    for i, item in enumerate(setlist):
        if i > 0:
            check = is_current_release(
                setlist[i - 1]["release_date"], setlist[i]["release_date"]
            )
            if check == "*":
                return dict(item)

    print("Current release not found")
    return {}


def set_codes(include_all_sets=False) -> list:
    endpoint = "/sets"

    sleep(0.1)  # just in case we ever call this in a loop

    try:
        req_url = url + endpoint
        res = requests.get(req_url, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()

        response = res.json()

        show_warnings(response)

        if res.status_code == 200:
            setlist_data = response.get("data")

            setlist = []

            for set_info in setlist_data:
                released = set_info.get("released_at")
                set_type = set_info.get("set_type")
                # define the types of sets to show (expansion, core, draft_innovation
                # seem to be the main ones)
                main_sets = [
                    "expansion",
                    "commander",
                    "draft_innovation",
                    "core",
                    "masters",
                    "arsenal",
                ]
                values_to_store = {
                    "set_code": set_info.get("code").upper(),
                    "name": set_info.get("name"),
                    "release_date": released,
                    # "set_type": set_info.get("set_type"),
                    "card_count": set_info.get("card_count"),
                }
                # if include_all_sets flag given, store all sets,
                # otherwise filter to main_sets
                if include_all_sets:
                    setlist.append(values_to_store)
                elif set_type in main_sets:
                    setlist.append(values_to_store)
            return setlist
        else:
            print(
                "Something may have gone wrong getting the list of sets... Status Code: ",
                res.status_code,
            )
            return []
    except requests.exceptions.RequestException as err:
        print("Setlist ERROR: ", err)
        return []


def get_set_info(set_code: str) -> dict:
    endpoint = "/sets/"

    sleep(0.1)  # just in case we ever call this in a loop

    try:
        req_url = url + endpoint + set_code
        res = requests.get(req_url, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()

        response = res.json()

        show_warnings(response)

        if res.status_code == 200:
            return response
        else:
            print(
                "Something may have gone wrong getting info about the set. Status Code: ",
                res.status_code,
            )
            return {}
    except requests.exceptions.RequestException as err:
        print("Setlist ERROR: ", err)
        return {}
