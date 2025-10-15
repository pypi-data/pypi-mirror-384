import math


# HACK: when a list request is made from scryfall, cards are added to db with that timestamp added
# this timestamp is them used to filter queries from db... this means that cards are always added
# from scryfall before stats are queried, even if they're already in the db.
# PRO: this means the cards are always up to date (and accurate, i.e. in a set query, it means we
# have the full set, rather than a partial that may already exist in db)
# CON: unecessary requests from db, inefficient
# could a different command (local_stats?) check the db WITHOUT using the timestamp method?
# (this would mean redesigning all the db queries...)
#
# BUG: if stats are called on a cleared (empty) db, we get an error.
#
def db_stats(connection, stamp=None) -> list:

    try:
        stats = []

        timestamp_query = ""
        if stamp is not None:
            timestamp_query = f"WHERE added_at = '{stamp}'"

        # print("timestamp_query: ", timestamp_query)
        total_cards = get_total_cards(connection, stamp)
        # stats.append(f"Stats for {total_cards} cards")

        cursor = connection.cursor()

        # Mana Curve of CMC
        cursor.execute(
            f"SELECT cmc, COUNT(*) as Mana FROM cards {timestamp_query} GROUP BY cmc"
        )
        curve = cursor.fetchall()
        stats.append(f" MANA CURVE:\n{chart_data(curve, total_cards)}")

        # Colour distribution
        cursor.execute(
            f"""SELECT 
                value as color_identity,
                COUNT(*) AS color_count
                FROM cards,
                json_each(cards.color_identity) {timestamp_query}
                GROUP BY value
                ORDER BY color_count DESC
            """
        )
        curve = cursor.fetchall()
        coloured_results = [[scryfall_colours(id), count] for id, count in curve]

        stats.append(
            f" COLOUR DISTRIBUTION:\n{chart_data(coloured_results, total_cards)}"
        )

        # Rarity distribution
        cursor.execute(
            f"""SELECT
                rarity,
                COUNT(rarity) AS rarity_count
                FROM cards
                {timestamp_query}
                GROUP BY rarity
                ORDER BY rarity_count DESC
            """
        )
        curve = cursor.fetchall()
        stats.append(f" RARITY DISTRIBUTION:\n{chart_data(curve, total_cards)}")

        # Tally of card types
        cursor.execute(
            report_card_types(timestamp_query)[0], report_card_types(timestamp_query)[1]
        )
        curve = cursor.fetchall()
        stats.append(f" CARD TYPES:\n{chart_data(curve, total_cards)}")

        # Prices: highest and average
        stats.append(" PRICES:")
        price_info = report_prices(cursor, timestamp_query)
        stats.append(f"  Average Price is {price_info[1]} EUR")
        stats.append("\n".join(price_info[0]))
        stats.append("")
        return stats

    except Exception as err:
        return ["Error occured talking to database for DB stats:", {err}]


def get_total_cards(connection, timestamp=None) -> int | str:
    try:
        cursor = connection.cursor()

        if timestamp is None:
            cursor.execute("SELECT COUNT(1) FROM cards")
        else:
            cursor.execute(
                "SELECT COUNT(1) FROM cards WHERE added_at = ?", (timestamp,)
            )
        return cursor.fetchone()[0]
    except Exception as err:
        return f"Error occured talking to database getting Total: {err}"


def get_unique_cards(connection, timestamp=None) -> int | str:
    try:
        cursor = connection.cursor()

        if timestamp is None:
            cursor.execute("SELECT COUNT(1) FROM cards")
        else:
            cursor.execute(
                "SELECT COUNT(DISTINCT lower(name)) FROM cards WHERE added_at = ?",
                (timestamp,),
            )
        return cursor.fetchone()[0]
    except Exception as err:
        return f"Error occured talking to database getting Unique cards: {err}"


def chart_data(curve_data, total_cards) -> str:
    if total_cards < 1 or curve_data is False:
        return "Could not chart data. Not enough cards."
    print_curve = ""
    percentage_steps = 2  # each block is x%
    scale = 100 / total_cards

    # get longest key as string (just for formatting alignment)
    chart_keys = [str(x) for x, _ in curve_data]
    if chart_keys == []:
        return "Not enough keys for data."
    max_key_string_length = len(max(chart_keys, key=len))

    # scale the bar charts
    for item in curve_data:
        bar = ""
        n_blocks = math.ceil((item[1] * scale) / percentage_steps)
        for _ in range(n_blocks):
            bar += "░"  # ▒█
        # pad out the key to the longest string so the bar charts are aligned
        print_curve += (
            f"  {item[0]:>{max_key_string_length}}: {bar} ({item[1]} cards)\n"
        )
    return print_curve


def report_card_types(timestamp_query=None):
    if timestamp_query is None:
        timestamp_query = ""
    # chart card types based on type_line
    card_types = [
        "Artifact",
        "Creature",
        "Land",
        "Enchantment",
        "Sorcery",
        "Planeswalker",
        "Instant",
        "Legendary",
    ]
    value_placeholder = ",".join(["(?)"] * len(card_types))
    query = f"""
            WITH wanted(type) AS ( VALUES {value_placeholder} )
            SELECT 
                w.type AS bucket,
                COUNT(*) AS n
            FROM wanted w
            JOIN cards c
                ON INSTR(LOWER(COALESCE(c.type_line, '')), TRIM(LOWER(w.type))) > 0
            {timestamp_query}
            GROUP BY w.type
            ORDER BY n DESC;
        """
    return (query, card_types)


def report_prices(cursor, timestamp_query: str) -> tuple:
    # TODO: this only takes into account non-foil card prices... if foil prices are
    # available (not always), they should also be included and aaveraged, though it might
    # skew the hightest prices?
    cursor.execute(
        f"SELECT name, CAST(json_extract(price,'$.eur') AS REAL) AS price FROM cards {timestamp_query} ORDER BY price DESC LIMIT 9"
    )
    highest_price = cursor.fetchall()
    top_prices = []
    top_prices.append("  Most expensive cards:")
    # check for duplicate cards appearing in expensive list
    # this happens when variation prints are equally sought after
    # do not append duplicate cards to the top

    top_price_dict = {}
    for item in highest_price:
        if item[0] not in top_price_dict.keys():
            top_price_dict[item[0]] = item[1]
    for card, price in top_price_dict.items():
        if price is None:
            price = "---"
        else:
            price = round(price, 2)
        card_price_info = f"  - {card:<35} {price:>10} EUR"
        top_prices.append(card_price_info)
        if len(top_prices) == 4:  # stop after three top prices + 1 for heading
            break

    cursor.execute(
        f"SELECT AVG(CAST(json_extract(price,'$.eur') AS REAL)) FROM cards {timestamp_query}"
    )
    avg_price = cursor.fetchone()[0]
    if avg_price is None:
        avg_price = "No prices found"
    else:
        avg_price = round(avg_price, 2)

    return top_prices, avg_price


def scryfall_colours(reference: str) -> str:
    colour_codes = {"R": "Red", "G": "Green", "U": "Blue", "B": "Black", "W": "White"}
    return colour_codes.get(reference, "Unknown")
