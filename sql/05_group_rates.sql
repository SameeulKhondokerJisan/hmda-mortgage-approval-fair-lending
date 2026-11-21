-- Approval and denial rates by applicant group, overall and by loan type (core sample).
SELECT applicant_group,
       COALESCE(loan_type, 'All') AS loan_type,
       COUNT(*) AS applications,
       SUM(approved) AS approved,
       SUM(denied) AS denied,
       AVG(approved) AS approval_rate,
       AVG(denied) AS denial_rate,
       MEDIAN(income_k) AS median_income_k,
       MEDIAN(loan_amount) AS median_loan_amount,
       AVG(CASE WHEN dti_value >= 50 THEN 1.0 WHEN dti_value IS NOT NULL THEN 0.0 END) AS share_dti_50_plus,
       AVG(CASE WHEN ltv > 95 THEN 1.0 WHEN ltv IS NOT NULL THEN 0.0 END) AS share_ltv_over_95
FROM core
GROUP BY GROUPING SETS ((applicant_group), (applicant_group, loan_type))
ORDER BY loan_type, applications DESC
