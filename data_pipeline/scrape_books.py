import os
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
INR_PER_GBP = 105.50

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

CATEGORIES = {
    "Travel": "travel_2",
    "Mystery": "mystery_3",
    "Historical Fiction": "historical-fiction_4",
}


def get_category_url(category):
    """Return the Books to Scrape URL for a category."""
    category_slug = CATEGORIES[category]

    return (
        f"{BASE_URL}catalogue/category/books/"
        f"{category_slug}/index.html"
    )


def parse_price(price_text):
    """Convert a price string such as '£51.77' to a float."""
    try:
        cleaned = re.sub(r"[^\d.]", "", price_text)
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def parse_rating(star_rating):
    """Convert text rating One..Five to an integer 1..5."""
    return RATING_MAP.get(star_rating)


def parse_availability(availability_text):
    """Convert availability text to a boolean in-stock value."""
    if not isinstance(availability_text, str):
        return None

    return "in stock" in availability_text.lower()
def fix_text_encoding(text):
    """Fix common UTF-8 text decoded incorrectly as Windows-1252."""
    if not isinstance(text, str):
        return text

    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def scrape_category(category):
    """Scrape all available pages for one category."""
    books = []
    page_number = 1
    category_url = get_category_url(category)

    while True:
        if page_number == 1:
            url = category_url
        else:
            url = category_url.replace(
                "index.html",
                f"page-{page_number}.html",
            )

        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, "html.parser")

        book_cards = soup.select("article.product_pod")

        if not book_cards:
            break

        for book in book_cards:
            title_tag = book.select_one("h3 a")
            price_tag = book.select_one("p.price_color")
            rating_tag = book.select_one("p.star-rating")
            availability_tag = book.select_one(
                "p.instock.availability"
            )

            title = (
                title_tag.get("title", "").strip()
                if title_tag
                else None
            )

            price_text = (
                price_tag.get_text(strip=True)
                if price_tag
                else None
            )

            star_rating = (
                rating_tag.get("class", [])[-1]
                if rating_tag and len(rating_tag.get("class", [])) > 1
                else None
            )

            availability = (
                availability_tag.get_text(" ", strip=True)
                if availability_tag
                else None
            )

            books.append(
                {
                    "title": title,
                    "price": price_text,
                    "star_rating": star_rating,
                    "availability": availability,
                    "category": category,
                }
            )

        next_button = soup.select_one("li.next a")

        if next_button is None:
            break

        page_number += 1

    return books


def clean_data(df):
    """Clean scraped fields and create required derived columns."""

    df = df.copy()
    df["title"] = df["title"].apply(fix_text_encoding)
    # Parse GBP price.
    df["price_gbp"] = df["price"].apply(parse_price)

    # Parse text rating into integer 1..5.
    df["rating"] = df["star_rating"].apply(parse_rating)

    # Parse availability text into boolean.
    df["in_stock"] = df["availability"].apply(parse_availability)

    # Handle numeric parsing failures using median imputation.
    if df["price_gbp"].isna().any():
        median_price = df["price_gbp"].median()

        if pd.isna(median_price):
            raise ValueError(
                "Price parsing failed and no median price is available."
            )

        df["price_gbp"] = df["price_gbp"].fillna(median_price)

    if df["rating"].isna().any():
        median_rating = df["rating"].median()

        if pd.isna(median_rating):
            raise ValueError(
                "Rating parsing failed and no median rating is available."
            )

        df["rating"] = (
            df["rating"]
            .fillna(median_rating)
            .round()
            .astype(int)
        )

    # Convert the fixed artificial exchange rate.
    df["price_inr"] = df["price_gbp"] * INR_PER_GBP

    return df


def main():
    all_books = []

    for category in CATEGORIES:
        print(f"Scraping category: {category}")

        category_books = scrape_category(category)

        print(
            f"  Books collected from {category}: "
            f"{len(category_books)}"
        )

        all_books.extend(category_books)

    if not all_books:
        raise RuntimeError(
            "No books were scraped. Check the website connection."
        )

    raw_df = pd.DataFrame(all_books)

    cleaned_df = clean_data(raw_df)

    os.makedirs("data_pipeline/data", exist_ok=True)
    os.makedirs("data_pipeline/outputs", exist_ok=True)

    raw_path = "data_pipeline/data/books_raw.csv"
    cleaned_path = "data_pipeline/outputs/books_cleaned.csv"

    raw_df.to_csv(raw_path, index=False)
    cleaned_df.to_csv(cleaned_path, index=False)

    print("\nScraping completed.")
    print(f"Raw rows: {len(raw_df)}")
    print(f"Cleaned rows: {len(cleaned_df)}")
    print(
        f"Categories: "
        f"{cleaned_df['category'].nunique()}"
    )

    print("\nCleaned columns:")
    print(cleaned_df.columns.tolist())

    print("\nMissing values:")
    print(cleaned_df.isna().sum())

    print("\nCategory counts:")
    print(cleaned_df["category"].value_counts())

    print("\nFirst five cleaned rows:")
    print(cleaned_df.head())

    print(f"\nSaved raw data to: {raw_path}")
    print(f"Saved cleaned data to: {cleaned_path}")


if __name__ == "__main__":
    main()