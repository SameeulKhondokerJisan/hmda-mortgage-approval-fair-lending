-- Grid for the Excel underwriting simulator: applications by group, DTI band and LTV band, with the
-- approvals and approved loan volume that a stricter cap would remove.
SELECT applicant_group, dti_band, ltv_band,
       COUNT(*) AS applications,
       SUM(approved) AS approved,
       SUM(denied) AS denied,
       COALESCE(SUM(loan_amount) FILTER (WHERE approved = 1), 0) AS approved_volume
FROM core
WHERE applicant_group IN ('White', 'Black', 'Hispanic', 'Asian', 'Other minority')
GROUP BY ALL
ORDER BY applicant_group, dti_band, ltv_band
