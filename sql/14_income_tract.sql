-- Applicant income band and census-tract minority share by applicant group (Power BI and figures).
SELECT applicant_group, income_band, tract_minority_band,
       COUNT(*) AS applications,
       SUM(approved) AS approved,
       SUM(denied) AS denied
FROM core
GROUP BY ALL
