# create SQLITE database and tables, insert into table


def create_table(connection):
    cursor = connection.cursor()
    schema = """
    CREATE TABLE IF NOT EXISTS cards(
    id TEXT PRIMARY KEY,
    name TEXT,
    type_line TEXT,
    oracle_text TEXT,
    color_identity TEXT,
    colors TEXT,
    set_code TEXT,
    mana_cost TEXT,
    cmc INTEGER, 
    price JSON,
    flavor_text TEXT,
    rarity TEXT,
    added_at TEXT 
    )
    """
    cursor.execute(schema)
    connection.commit()


def drop_table(connection) -> None:
    try:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS cards;")

    except Exception as err:
        print(f"Error clearing database: {err}")


def clear_database(connection) -> None:
    check = input("This will delete your database, are you sure? (y/N): ")
    if check.lower() == "y":
        drop_table(connection)
        print("Your database has been exiled to the graveyard and removed from game...")
    else:
        print("Damnation avoided.")
