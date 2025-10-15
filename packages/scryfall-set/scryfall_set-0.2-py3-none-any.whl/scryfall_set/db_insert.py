import json
from datetime import datetime


def insert_cards(cards: list, timestamp: datetime, connection) -> int:
    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT OR REPLACE INTO cards (
            id, name, type_line, oracle_text, color_identity, colors,
            set_code, mana_cost, cmc, price, flavor_text, rarity, added_at )
            VALUES (
            :id, :name, :type_line, :oracle_text, :color_identity, :colors,
            :set_code, :mana_cost, :cmc, :price, :flavor_text, :rarity, :added_at )
            """
        rows = [transform_card(raw_card, timestamp) for raw_card in cards]
        cursor.executemany(insert_query, rows)
        connection.commit()

        return len(cards)
    except Exception as err:
        print(f"Error occured talking to database: {err}")
        return 0


def transform_card(card_data: dict, timestamp: datetime) -> dict:
    return {
        "id": card_data["id"],
        "name": card_data["name"],
        "type_line": card_data["type_line"].title(),
        "oracle_text": card_data.get("oracle_text", ""),
        "color_identity": json.dumps(card_data.get("color_identity", {})),
        "colors": json.dumps(card_data.get("colors", {})),
        "set_code": card_data.get("set", "").upper(),
        "mana_cost": card_data.get("mana_cost", ""),
        "cmc": card_data["cmc"],
        "price": json.dumps(card_data.get("prices", {})),
        "flavor_text": card_data.get("flavor_text", ""),
        "rarity": card_data.get("rarity", "").title(),
        "added_at": timestamp,
    }
