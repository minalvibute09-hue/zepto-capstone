import os
import sqlite3

import pandas as pd


CLEANED_DATA_PATH = "data_pipeline/outputs/books_cleaned.csv"
DATABASE_PATH = "data_pipeline/data/books.db"


def create_database():
    """Create a normalized SQLite database from the cleaned book data."""

    if not os.path.exists(CLEANED_DATA_PATH):
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CLEANED_DATA_PATH}"
        )

    df = pd.read_csv(CLEANED_DATA_PATH)

    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        # Start fresh so the schema is reproducible.
        cursor.executescript(
            """
            DROP TABLE IF EXISTS books;
            DROP TABLE IF EXISTS categories;

            CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price_gbp REAL NOT NULL,
                rating INTEGER NOT NULL,
                in_stock INTEGER NOT NULL,
                price_inr REAL NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id)
                    REFERENCES categories(category_id)
            );
            """
        )

        # Insert unique categories first.
        categories = (
            df[["category"]]
            .drop_duplicates()
            .sort_values("category")
        )

        for category_name in categories["category"]:
            cursor.execute(
                """
                INSERT INTO categories (category_name)
                VALUES (?)
                """,
                (category_name,),
            )

        # Map category names to their generated primary keys.
        category_map = dict(
            cursor.execute(
                "SELECT category_name, category_id FROM categories"
            ).fetchall()
        )

        # Insert books using the category foreign key.
        for _, row in df.iterrows():
            cursor.execute(
                """
                INSERT INTO books (
                    title,
                    price_gbp,
                    rating,
                    in_stock,
                    price_inr,
                    category_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["title"],
                    row["price_gbp"],
                    int(row["rating"]),
                    int(bool(row["in_stock"])),
                    row["price_inr"],
                    category_map[row["category"]],
                ),
            )

        connection.commit()

        print("SQLite database created successfully.")
        print(f"Database: {DATABASE_PATH}")
        print("Tables: categories, books")
        print(f"Categories inserted: {len(categories)}")
        print(f"Books inserted: {len(df)}")

    finally:
        connection.close()


if __name__ == "__main__":
    create_database()
    