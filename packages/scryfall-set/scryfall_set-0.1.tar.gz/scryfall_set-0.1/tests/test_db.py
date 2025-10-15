import sqlite3
import datetime
from src.scryfall_set.db_setup import create_table
from src.scryfall_set.db_insert import insert_cards
from tests.sample_card import sample_card
from pathlib import Path
from contextlib import closing


def test_card_insert_and_get():
    path_test_db = Path(__file__).parent
    with closing(sqlite3.connect(Path(path_test_db) / "tests.db")) as connection:

        create_table(connection)

        assert insert_cards([sample_card()], datetime.datetime.now(), connection) == 1
        # this should return 1 (the single card added)

        # pull first row from test db, then check that it is Llanowar
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM cards")
        card = cursor.fetchone()

        assert card[0] == "6a0b230b-d391-4998-a3f7-7b158a0ec2cd"  # id
        assert card[1] == "Llanowar Elves"  # name
        assert card[2] == "Creature — Elf Druid"  # type_line
        assert card[3] == "{T}: Add {G}."  # oracle_text
        assert card[4] == '["G"]'  # color_identity
        assert card[5] == '["G"]'  # colors
        assert card[6] == "FDN"  # set
        assert card[7] == "{G}"  # mana_cost
        assert card[8] == 1.0  # cmc

        cursor.execute("DROP TABLE cards;")
        # TODO: look into pytest's fixtures for automatic teardown/cleanup
