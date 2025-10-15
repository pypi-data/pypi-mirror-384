from src.scryfall_set.request import get_random_card


def test_random_card_request():
    random_card = get_random_card("")

    # since we're pulling a random card, there's not many
    # specifics we can assert other than object == card.

    assert random_card
    assert isinstance(random_card, list)
    assert len(random_card) == 1
    assert random_card[0].get("object") == "card"
    assert isinstance(random_card[0].get("name"), str)
    assert isinstance(random_card[0].get("id"), str)
