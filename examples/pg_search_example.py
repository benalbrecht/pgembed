import tempfile
import pgembed
import sqlalchemy as sa
from sqlalchemy_utils import database_exists, create_database


def test_pg_search():
    if not pgembed.has_extension("pg_search"):
        raise RuntimeError(
            "pg_search extension is not installed. Install pgembed-pgsearch or build with 'make EXTENSIONS=pg_search'."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        with pgembed.get_server(
            tmpdir,
            shared_preload_libraries=["pg_search"],
        ) as pg:
            database_name = "testdb"
            uri = pg.get_uri(database_name)

            if not database_exists(uri):
                create_database(uri)

            engine = sa.create_engine(uri, isolation_level="AUTOCOMMIT")
            conn = engine.connect()

            with conn.begin():
                conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_search CASCADE;"))
                conn.execute(
                    sa.text("""
                    DROP TABLE IF EXISTS items;
                    CREATE TABLE items (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        description TEXT
                    );
                """)
                )

                data = [
                    ("Python Search", "A guide to searching with Python and Postgres"),
                    ("Postgres Tutorial", "Learn full text search in Postgres"),
                    ("Database Optimization", "Tips for better database performance"),
                ]
                for title, desc in data:
                    conn.execute(
                        sa.text("""
                        INSERT INTO items (title, description)
                        VALUES (:title, :desc)
                    """),
                        {"title": title, "desc": desc},
                    )

                conn.execute(
                    sa.text("""
                    CREATE INDEX items_search_idx ON items
                    USING bm25 (id, title, description)
                    WITH (key_field = 'id');
                """)
                )

                search_query = "Python Postgres"
                print(f"Searching for: '{search_query}'\n")

                result = conn.execute(
                    sa.text("""
                    SELECT title, description, pdb.score(id) AS score
                    FROM items
                    WHERE description ||| :query OR title ||| :query
                    ORDER BY score DESC;
                """),
                    {"query": search_query},
                )

                results = result.fetchall()
                for row in results:
                    print(f"Result: {row[0]} - {row[1]} (score={row[2]:.4f})")

            conn.close()


if __name__ == "__main__":
    test_pg_search()
