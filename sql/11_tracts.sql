-- Neighbourhood view: denial rate by the minority share and relative income of the census tract.
SELECT tract_minority_band,
       tract_income_band,
       COUNT(*) AS applications,
       AVG(denied) AS denial_rate,
       MEDIAN(income_k) AS median_income_k
FROM core
WHERE tract_minority_band <> '6 Unknown' AND tract_income_band <> '5 Unknown'
GROUP BY ALL
ORDER BY tract_minority_band, tract_income_band
