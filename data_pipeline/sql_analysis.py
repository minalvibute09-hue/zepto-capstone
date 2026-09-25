import sqlite3
import pandas as pd

DATABASE_PATH = "data_pipeline/data/books.db"


def run_sql_analysis():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        print("=" * 70)
        print("QUERY 1: SELECT + WHERE")
        print("=" * 70)

        query_1 = """
        SELECT title, price_gbp, rating
        FROM books
        WHERE rating >= 4
        ORDER BY rating DESC, price_gbp DESC;
        """

        result_1 = pd.read_sql(query_1, connection)
        print(result_1.head(10).to_string(index=False))

        print("\n" + "=" * 70)
        print("QUERY 2: ORDER BY + LIMIT")
        print("=" * 70)

        query_2 = """
        SELECT title, price_gbp
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10;
        """

        result_2 = pd.read_sql(query_2, connection)
        print(result_2.to_string(index=False))

        print("\n" + "=" * 70)
        print("QUERY 3: DISTINCT")
        print("=" * 70)

        query_3 = """
        SELECT DISTINCT rating
        FROM books
        ORDER BY rating;
        """

        result_3 = pd.read_sql(query_3, connection)
        print(result_3.to_string(index=False))

        print("\n" + "=" * 70)
        print("QUERY 4: IN")
        print("=" * 70)

        query_4 = """
        SELECT title, rating
        FROM books
        WHERE rating IN (4, 5)
        ORDER BY rating DESC, title;
        """

        result_4 = pd.read_sql(query_4, connection)
        print(result_4.head(10).to_string(index=False))

        print("\n" + "=" * 70)
        print("QUERY 5: BETWEEN")
        print("=" * 70)

        query_5 = """
        SELECT title, price_gbp
        FROM books
        WHERE price_gbp BETWEEN 10 AND 30
        ORDER BY price_gbp;
        """

        result_5 = pd.read_sql(query_5, connection)
        print(result_5.head(10).to_string(index=False))

        print("\n" + "=" * 70)
        print("QUERY 6: JOIN")
        print("=" * 70)

        query_join = """
        SELECT
            b.book_id,
            b.title,
            c.category_name,
            b.price_gbp,
            b.rating
        FROM books AS b
        JOIN categories AS c
            ON b.category_id = c.category_id
        ORDER BY c.category_name, b.title;
        """

        join_result = pd.read_sql(query_join, connection)

        print("SQL JOIN result:")
        print(join_result.head(10).to_string(index=False))

        print("\n" + "=" * 70)
        print("EQUIVALENT JOIN USING pd.merge")
        print("=" * 70)

        books_df = pd.read_sql(
            """
            SELECT
                book_id,
                title,
                price_gbp,
                rating,
                category_id
            FROM books
            """,
            connection,
        )

        categories_df = pd.read_sql(
            """
            SELECT
                category_id,
                category_name
            FROM categories
            """,
            connection,
        )

        merge_result = pd.merge(
            books_df,
            categories_df,
            on="category_id",
            how="inner",
        )

        merge_result = merge_result[
            [
                "book_id",
                "title",
                "category_name",
                "price_gbp",
                "rating",
            ]
        ].sort_values(
            ["category_name", "title"]
        ).reset_index(drop=True)

        print("pd.merge result:")
        print(merge_result.head(10).to_string(index=False))

        sql_sorted = join_result.sort_values(
            ["category_name", "title"]
        ).reset_index(drop=True)

        print("\n" + "=" * 70)
        print("JOIN EQUIVALENCE CHECK")
        print("=" * 70)

        print("Same shape:", sql_sorted.shape == merge_result.shape)
        print("Same values:", sql_sorted.equals(merge_result))

        if not sql_sorted.equals(merge_result):
            raise AssertionError(
                "SQL JOIN and pandas merge results are not equivalent."
            )

        print("SQL JOIN and pandas merge produce equivalent outputs.")

    finally:
        connection.close()


if __name__ == "__main__":
    run_sql_analysis()