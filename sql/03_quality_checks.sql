-- Data-quality rules. Hard rules stop the pipeline; soft rules are expected features of HMDA data
-- that the analysis handles (see docs/methodology.md). failures = rows breaking the rule.
SELECT * FROM (
    SELECT 'Row count at least {min_rows_fmt}' AS rule, 'hard' AS severity,
           CASE WHEN COUNT(*) >= {min_rows} THEN 0 ELSE 1 END AS failures FROM lar_raw
    UNION ALL
    SELECT 'Activity year is 2025', 'hard', COUNT(*) FILTER (WHERE activity_year <> '2025') FROM lar_raw
    UNION ALL
    SELECT 'Loan purpose is home purchase (1)', 'hard', COUNT(*) FILTER (WHERE loan_purpose <> '1') FROM lar_raw
    UNION ALL
    SELECT 'Action taken is 1, 2 or 3', 'hard', COUNT(*) FILTER (WHERE action_taken NOT IN ('1', '2', '3')) FROM lar_raw
    UNION ALL
    SELECT 'LEI is 20 characters', 'hard', COUNT(*) FILTER (WHERE length(lei) <> 20 OR lei IS NULL) FROM lar_raw
    UNION ALL
    SELECT 'Loan amount is a positive number', 'hard',
           COUNT(*) FILTER (WHERE TRY_CAST(loan_amount AS DOUBLE) IS NULL OR TRY_CAST(loan_amount AS DOUBLE) <= 0)
    FROM lar_raw
    UNION ALL
    SELECT 'Debt-to-income uses the published codes', 'hard',
           COUNT(*) FILTER (WHERE debt_to_income_ratio NOT IN ('<20%', '20%-<30%', '30%-<36%', '50%-60%', '>60%',
                                                               'NA', 'Exempt')
                             AND TRY_CAST(debt_to_income_ratio AS INTEGER) NOT BETWEEN 36 AND 49)
    FROM lar_raw
    UNION ALL
    SELECT 'Denied applications list a denial reason (exempt reporters excluded)', 'soft',
           COUNT(*) FILTER (WHERE action_taken = '3' AND "denial_reason-1" IN ('10', ''))
    FROM lar_raw
    UNION ALL
    SELECT 'Every lender LEI has a name in the filers list', 'soft',
           COUNT(*) FILTER (WHERE lei NOT IN (SELECT lei FROM lenders)) FROM lar_raw
    UNION ALL
    SELECT 'Income missing or not positive', 'soft',
           COUNT(*) FILTER (WHERE TRY_CAST(income AS DOUBLE) IS NULL OR TRY_CAST(income AS DOUBLE) <= 0) FROM lar_raw
    UNION ALL
    SELECT 'Loan-to-value missing, exempt or outside 1-250%', 'soft',
           COUNT(*) FILTER (WHERE TRY_CAST(loan_to_value_ratio AS DOUBLE) IS NULL
                             OR TRY_CAST(loan_to_value_ratio AS DOUBLE) NOT BETWEEN 1 AND 250) FROM lar_raw
    UNION ALL
    SELECT 'Debt-to-income NA or exempt', 'soft',
           COUNT(*) FILTER (WHERE debt_to_income_ratio IN ('NA', 'Exempt')) FROM lar_raw
    UNION ALL
    SELECT 'Race or ethnicity not reported', 'soft',
           COUNT(*) FILTER (WHERE derived_race IN ('Race Not Available', 'Free Form Text Only')
                             OR derived_ethnicity IN ('Ethnicity Not Available', 'Free Form Text Only')) FROM lar_raw
    UNION ALL
    SELECT 'Partially exempt reporter (1111 codes)', 'soft',
           COUNT(*) FILTER (WHERE business_or_commercial_purpose = '1111' OR "open-end_line_of_credit" = '1111')
    FROM lar_raw
    UNION ALL
    SELECT 'County code missing', 'soft', COUNT(*) FILTER (WHERE NOT regexp_full_match(county_code, '\d{5}'))
    FROM lar_raw
    UNION ALL
    SELECT 'Identical public records (public file has no application ID)', 'soft', COUNT(*) - COUNT(DISTINCT lar_raw) FROM lar_raw
)
