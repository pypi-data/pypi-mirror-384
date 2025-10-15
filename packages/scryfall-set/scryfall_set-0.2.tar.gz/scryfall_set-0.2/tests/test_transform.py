# test the clean-up/transofrm of card data ready for inserting into

import datetime
from src.scryfall_set.db_insert import transform_card
from tests.sample_card import sample_card


def test_transform_card_pulls_correct_values():

    card = transform_card(sample_card(), datetime.datetime.now())

    assert card["id"] == "6a0b230b-d391-4998-a3f7-7b158a0ec2cd"  # id
    assert card["name"] == "Llanowar Elves"  # name
    assert card["type_line"] == "Creature — Elf Druid"  # type_line
    assert card["oracle_text"] == "{T}: Add {G}."  # oracle_text
    assert card["color_identity"] == '["G"]'  # color_identity
    assert card["colors"] == '["G"]'  # colors
    assert card["set_code"] == "FDN"  # set
    assert card["mana_cost"] == "{G}"  # mana_cost
    assert card["cmc"] == 1.0  # cmc
    assert (
        card["price"]
        == '{"usd": "0.23", "usd_foil": "3.20", "usd_etched": null, "eur": "0.22", "eur_foil": "0.37", "tix": "0.03"}'
    )  # prices
    assert (
        card["flavor_text"]
        == "The elves of the Llanowar forest have defended it for generations. It is their sacred duty to keep outside influences from corrupting their ancestral home."
    )  # flavor_text
    assert type(card["added_at"]) is datetime.datetime  # timestamp
