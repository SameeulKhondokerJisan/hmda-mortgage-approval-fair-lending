-- Lender benchmark (core sample): volume, outcomes, applicant mix and pricing of originated
-- conventional 30-year fixed loans.
SELECT a.lei,
       COALESCE(l.lender_name, a.lei) AS lender_name,
       COUNT(*) AS applications,
       SUM(originated) AS originations,
       SUM(loan_amount) FILTER (WHERE originated = 1) AS originated_volume,
       AVG(approved) AS approval_rate,
       AVG(denied) AS denial_rate,
       AVG((applicant_group = 'Black')::INT) AS share_black,
       AVG((applicant_group = 'Hispanic')::INT) AS share_hispanic,
       AVG(denied) FILTER (WHERE applicant_group = 'White') AS denial_rate_white,
       AVG(denied) FILTER (WHERE applicant_group = 'Black') AS denial_rate_black,
       AVG(denied) FILTER (WHERE applicant_group = 'Hispanic') AS denial_rate_hispanic,
       COUNT(*) FILTER (WHERE applicant_group = 'Black') AS apps_black,
       COUNT(*) FILTER (WHERE applicant_group = 'Hispanic') AS apps_hispanic,
       AVG((loan_type = 'FHA')::INT) AS share_fha,
       MEDIAN(rate_spread) FILTER (WHERE originated = 1 AND loan_type = 'Conventional' AND loan_term = 360
                                   AND fixed_amortizing) AS median_rate_spread
FROM core a LEFT JOIN lenders l USING (lei)
GROUP BY a.lei, l.lender_name
ORDER BY applications DESC
