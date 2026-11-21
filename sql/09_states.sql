-- State view (core sample): denial rates by group.
SELECT state_code,
       COUNT(*) AS applications,
       AVG(denied) AS denial_rate,
       AVG(denied) FILTER (WHERE applicant_group = 'White') AS denial_rate_white,
       AVG(denied) FILTER (WHERE applicant_group = 'Black') AS denial_rate_black,
       AVG(denied) FILTER (WHERE applicant_group = 'Hispanic') AS denial_rate_hispanic,
       COUNT(*) FILTER (WHERE applicant_group = 'Black') AS apps_black,
       COUNT(*) FILTER (WHERE applicant_group = 'Hispanic') AS apps_hispanic,
       MEDIAN(loan_amount) AS median_loan_amount
FROM core
WHERE state_code IS NOT NULL
GROUP BY state_code
ORDER BY applications DESC
