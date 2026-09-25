import os
import sqlite3

import pandas as pd


CLEANED_DATA_PATH = "data_pipeline/outputs/books_cleaned.csv"
DATABASE_PATH = "data_pipeline/data/books.db"


def create_database():
    """Load the cleaned book data into a SQLite database."""

    if not os.path.exists(CLEANED_DATA_PATH):
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CLEANED_DATA_PATH}"
        )

    df = pd.read_csv(CLEANED_DATA_PATH)

    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        df.to_sql(
            "books",
            connection,
            if_exists="replace",
            index=False,
        )
    finally:
        connection.close()

    print("SQLite database created successfully.")
    print(f"Database: {DATABASE_PATH}")
    print(f"Table: books")
    print(f"Rows inserted: {len(df)}")


if __name__ == "__main__":
    create_database()