-- Denial rate at each reported debt-to-income value. HMDA publishes 36% to 49% as exact values and the rest
-- in bands, so the 49% -> 50-60% step shows the effect of the 50% automated-underwriting limit.
SELECT loan_type,
       dti_value,
       dti_band,
       COUNT(*) AS applications,
       AVG(denied) AS denial_rate,
       AVG(CASE WHEN denied = 1 THEN list_contains([denial_reason_1, denial_reason_2, denial_reason_3, denial_reason_4], 1)::INT END)
           AS share_of_denials_citing_dti
FROM core
WHERE loan_type IN ('Conventional', 'FHA', 'VA') AND dti_value IS NOT NULL
GROUP BY loan_type, dti_value, dti_band
ORDER BY loan_type, dti_value
