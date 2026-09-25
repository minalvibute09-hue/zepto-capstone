-- Query 1: SELECT + WHERE
SELECT title, price_gbp, rating
FROM books
WHERE rating >= 4
ORDER BY rating DESC, price_gbp DESC;


-- Query 2: ORDER BY + LIMIT
SELECT title, price_gbp
FROM books
ORDER BY price_gbp DESC
LIMIT 10;


-- Query 3: DISTINCT
SELECT DISTINCT rating
FROM books
ORDER BY rating;


-- Query 4: IN
SELECT title, rating
FROM books
WHERE rating IN (4, 5)
ORDER BY rating DESC, title;


-- Query 5: BETWEEN
SELECT title, price_gbp
FROM books
WHERE price_gbp BETWEEN 10 AND 30
ORDER BY price_gbp;


-- Query 6: JOIN
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