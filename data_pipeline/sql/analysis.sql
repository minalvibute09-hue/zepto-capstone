-- 1. Average price by category
SELECT
    category,
    ROUND(AVG(price_inr), 2) AS average_price_inr
FROM books
GROUP BY category
ORDER BY average_price_inr DESC;
-- 2. Count of books by rating
SELECT
    rating,
    COUNT(*) AS book_count
FROM books
GROUP BY rating
ORDER BY rating;
-- 3. Top 10 most expensive books
SELECT
    title,
    category,
    ROUND(price_inr, 2) AS price_inr
FROM books
ORDER BY price_inr DESC
LIMIT 10;
-- 4. Price distribution buckets
SELECT
    CASE
        WHEN price_inr < 2000 THEN 'Below ₹2,000'
        WHEN price_inr < 4000 THEN '₹2,000–₹3,999'
        WHEN price_inr < 6000 THEN '₹4,000–₹5,999'
        ELSE '₹6,000+'
    END AS price_bucket,
    COUNT(*) AS book_count
FROM books
GROUP BY
    CASE
        WHEN price_inr < 2000 THEN 'Below ₹2,000'
        WHEN price_inr < 4000 THEN '₹2,000–₹3,999'
        WHEN price_inr < 6000 THEN '₹4,000–₹5,999'
        ELSE '₹6,000+'
    END
ORDER BY
    CASE
        WHEN price_bucket = 'Below ₹2,000' THEN 1
        WHEN price_bucket = '₹2,000–₹3,999' THEN 2
        WHEN price_bucket = '₹4,000–₹5,999' THEN 3
        WHEN price_bucket = '₹6,000+' THEN 4
    END;
    -- 5. Additional business question:
-- Which category has the highest average rating,
-- and how many books does each category contain?
SELECT
    category,
    ROUND(AVG(rating), 2) AS average_rating,
    COUNT(*) AS book_count
FROM books
GROUP BY category
ORDER BY average_rating DESC;