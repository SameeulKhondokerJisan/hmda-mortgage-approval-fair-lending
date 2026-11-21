-- Share of denied applications citing each reason (up to four reasons per application), by applicant group.
WITH reasons AS (
    SELECT applicant_group, app_id, r AS reason
    FROM core,
         LATERAL (SELECT unnest([denial_reason_1, denial_reason_2, denial_reason_3, denial_reason_4]) AS r)
    WHERE denied = 1 AND r BETWEEN 1 AND 9
),
denied AS (
    SELECT applicant_group, COUNT(*) AS denied_apps
    FROM core WHERE denied = 1 AND denial_reason_1 BETWEEN 1 AND 9 GROUP BY 1
)
SELECT r.applicant_group,
       CASE r.reason WHEN 1 THEN 'Debt-to-income ratio' WHEN 2 THEN 'Employment history' WHEN 3 THEN 'Credit history'
                     WHEN 4 THEN 'Collateral' WHEN 5 THEN 'Insufficient cash' WHEN 6 THEN 'Unverifiable information'
                     WHEN 7 THEN 'Credit application incomplete' WHEN 8 THEN 'Mortgage insurance denied'
                     ELSE 'Other' END AS reason,
       COUNT(DISTINCT r.app_id) AS denied_citing,
       d.denied_apps,
       COUNT(DISTINCT r.app_id) / d.denied_apps AS share_of_denials
FROM reasons r JOIN denied d USING (applicant_group)
GROUP BY r.applicant_group, r.reason, d.denied_apps
ORDER BY r.applicant_group, share_of_denials DESC
