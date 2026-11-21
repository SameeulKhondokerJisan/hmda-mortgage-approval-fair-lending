-- Decision funnel for the core sample (first-lien, owner-occupied, site-built 1-4 unit home purchase),
-- by loan type and in total.
SELECT COALESCE(loan_type, 'All') AS loan_type,
       COUNT(*) AS applications,
       SUM(approved) AS approved,
       SUM(originated) AS originated,
       SUM(denied) AS denied,
       AVG(denied) AS denial_rate,
       SUM(loan_amount) FILTER (WHERE originated = 1) AS originated_volume,
       MEDIAN(loan_amount) AS median_loan_amount,
       MEDIAN(income_k) AS median_income_k
FROM core
GROUP BY ROLLUP (loan_type)
ORDER BY applications DESC
