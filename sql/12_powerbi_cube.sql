-- Aggregated fact table for Power BI: core applications by state, loan type, applicant group and the two
-- main underwriting bands. Sums only, so every rate in the report is a ratio of sums.
SELECT state_code, loan_type, applicant_group, dti_band, ltv_band,
       COUNT(*) AS applications,
       SUM(approved) AS approved,
       SUM(denied) AS denied,
       SUM(originated) AS originated,
       COALESCE(SUM(loan_amount) FILTER (WHERE originated = 1), 0) AS originated_volume
FROM core
WHERE state_code IS NOT NULL
GROUP BY ALL
