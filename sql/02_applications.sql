-- Typed, labelled application table. One row per application with a credit decision
-- (action 1 originated, 2 approved but not accepted, 3 denied). Codes follow the 2025 HMDA filing
-- instructions; 'NA' and 'Exempt' become NULL. Bands are prefixed with a sort key for dashboards.
CREATE OR REPLACE TABLE applications AS
WITH typed AS (
    SELECT
        row_number() OVER () AS app_id,
        lei,
        NULLIF(state_code, 'NA') AS state_code,
        CASE WHEN regexp_full_match(county_code, '\d{5}') THEN county_code END AS county_fips,
        CASE WHEN regexp_full_match(census_tract, '\d{11}') THEN census_tract END AS census_tract,
        "derived_msa-md" AS msa_md,
        CAST(action_taken AS INTEGER) AS action_taken,
        CASE loan_type WHEN '1' THEN 'Conventional' WHEN '2' THEN 'FHA' WHEN '3' THEN 'VA' WHEN '4' THEN 'USDA' END
            AS loan_type,
        (lien_status = '1' AND occupancy_type = '1'
         AND derived_dwelling_category = 'Single Family (1-4 Units):Site-Built'
         AND business_or_commercial_purpose = '2' AND reverse_mortgage = '2'
         AND "open-end_line_of_credit" = '2') AS core,
        CASE
            WHEN derived_ethnicity = 'Hispanic or Latino' THEN 'Hispanic'
            WHEN derived_ethnicity = 'Joint' OR derived_race = 'Joint' THEN 'Joint'
            WHEN derived_ethnicity = 'Not Hispanic or Latino' AND derived_race = 'White' THEN 'White'
            WHEN derived_ethnicity = 'Not Hispanic or Latino' AND derived_race = 'Black or African American' THEN 'Black'
            WHEN derived_ethnicity = 'Not Hispanic or Latino' AND derived_race = 'Asian' THEN 'Asian'
            WHEN derived_ethnicity = 'Not Hispanic or Latino'
                 AND derived_race IN ('American Indian or Alaska Native', 'Native Hawaiian or Other Pacific Islander',
                                      '2 or more minority races') THEN 'Other minority'
            ELSE 'Not reported'
        END AS applicant_group,
        CASE derived_sex WHEN 'Sex Not Available' THEN 'Not reported' ELSE derived_sex END AS sex,
        CASE applicant_age WHEN '8888' THEN 'Not reported' WHEN '9999' THEN 'Not reported' ELSE applicant_age END
            AS age_band,
        CASE WHEN TRY_CAST(income AS DOUBLE) > 0 THEN TRY_CAST(income AS DOUBLE) END AS income_k,
        TRY_CAST(loan_amount AS DOUBLE) AS loan_amount,
        CASE WHEN TRY_CAST(property_value AS DOUBLE) > 0 THEN TRY_CAST(property_value AS DOUBLE) END AS property_value,
        CASE WHEN TRY_CAST(loan_to_value_ratio AS DOUBLE) BETWEEN 1 AND 250
             THEN TRY_CAST(loan_to_value_ratio AS DOUBLE) END AS ltv,
        debt_to_income_ratio AS dti_raw,
        TRY_CAST(debt_to_income_ratio AS INTEGER) AS dti_exact,
        TRY_CAST(interest_rate AS DOUBLE) AS interest_rate,
        TRY_CAST(rate_spread AS DOUBLE) AS rate_spread,
        TRY_CAST(total_loan_costs AS DOUBLE) AS total_loan_costs,
        TRY_CAST(discount_points AS DOUBLE) AS discount_points,
        TRY_CAST(loan_term AS INTEGER) AS loan_term,
        intro_rate_period = 'NA' AND balloon_payment = '2' AND interest_only_payment = '2'
            AND negative_amortization = '2' AND other_nonamortizing_features = '2' AS fixed_amortizing,
        CASE conforming_loan_limit WHEN 'C' THEN 1 WHEN 'NC' THEN 0 END AS conforming,
        CAST(preapproval = '1' AS INTEGER) AS preapproval,
        CAST(submission_of_application = '1' AS INTEGER) AS direct_application,
        applicant_credit_score_type AS credit_model,
        "aus-1" AS aus,
        TRY_CAST("denial_reason-1" AS INTEGER) AS denial_reason_1,
        TRY_CAST("denial_reason-2" AS INTEGER) AS denial_reason_2,
        TRY_CAST("denial_reason-3" AS INTEGER) AS denial_reason_3,
        TRY_CAST("denial_reason-4" AS INTEGER) AS denial_reason_4,
        TRY_CAST(tract_minority_population_percent AS DOUBLE) AS tract_minority_pct,
        TRY_CAST(tract_to_msa_income_percentage AS DOUBLE) AS tract_income_pct,
        TRY_CAST(ffiec_msa_md_median_family_income AS DOUBLE) AS area_median_income
    FROM lar_raw
)
SELECT
    *,
    CAST(action_taken IN (1, 2) AS INTEGER) AS approved,
    CAST(action_taken = 3 AS INTEGER) AS denied,
    CAST(action_taken = 1 AS INTEGER) AS originated,
    CASE
        WHEN dti_raw = '<20%' THEN '1 <20%'
        WHEN dti_raw = '20%-<30%' THEN '2 20-29%'
        WHEN dti_raw = '30%-<36%' THEN '3 30-35%'
        WHEN dti_exact BETWEEN 36 AND 39 THEN '4 36-39%'
        WHEN dti_exact BETWEEN 40 AND 44 THEN '5 40-44%'
        WHEN dti_exact BETWEEN 45 AND 49 THEN '6 45-49%'
        WHEN dti_raw = '50%-60%' THEN '7 50-60%'
        WHEN dti_raw = '>60%' THEN '8 >60%'
        ELSE '9 Missing'
    END AS dti_band,
    CASE
        WHEN dti_raw = '<20%' THEN 15 WHEN dti_raw = '20%-<30%' THEN 25 WHEN dti_raw = '30%-<36%' THEN 33
        WHEN dti_exact BETWEEN 36 AND 49 THEN dti_exact WHEN dti_raw = '50%-60%' THEN 55 WHEN dti_raw = '>60%' THEN 65
    END AS dti_value,
    CASE
        WHEN ltv IS NULL THEN '7 Missing'
        WHEN ltv <= 60 THEN '1 <=60%'
        WHEN ltv <= 80 THEN '2 60-80%'
        WHEN ltv <= 90 THEN '3 80-90%'
        WHEN ltv <= 95 THEN '4 90-95%'
        WHEN ltv <= 97 THEN '5 95-97%'
        ELSE '6 >97%'
    END AS ltv_band,
    CASE
        WHEN income_k IS NULL OR area_median_income IS NULL OR area_median_income = 0 THEN '5 Missing'
        WHEN income_k * 1000 / area_median_income < 0.5 THEN '1 Low (<50% of area median)'
        WHEN income_k * 1000 / area_median_income < 0.8 THEN '2 Moderate (50-80%)'
        WHEN income_k * 1000 / area_median_income < 1.2 THEN '3 Middle (80-120%)'
        ELSE '4 Upper (120%+)'
    END AS income_band,
    CASE
        WHEN tract_minority_pct IS NULL THEN '6 Unknown'
        WHEN tract_minority_pct < 10 THEN '1 <10%'
        WHEN tract_minority_pct < 30 THEN '2 10-30%'
        WHEN tract_minority_pct < 50 THEN '3 30-50%'
        WHEN tract_minority_pct < 80 THEN '4 50-80%'
        ELSE '5 80%+'
    END AS tract_minority_band,
    CASE
        WHEN tract_income_pct IS NULL OR tract_income_pct = 0 THEN '5 Unknown'
        WHEN tract_income_pct < 50 THEN '1 Low (<50%)'
        WHEN tract_income_pct < 80 THEN '2 Moderate (50-80%)'
        WHEN tract_income_pct < 120 THEN '3 Middle (80-120%)'
        ELSE '4 Upper (120%+)'
    END AS tract_income_band
FROM typed;

CREATE OR REPLACE VIEW core AS SELECT * FROM applications WHERE core;

-- Applications that carry every underwriting control used by the regressions.
CREATE OR REPLACE VIEW model_frame AS
SELECT * FROM core
WHERE applicant_group IN ('White', 'Black', 'Hispanic', 'Asian', 'Other minority')
  AND income_k IS NOT NULL AND loan_amount > 0 AND property_value IS NOT NULL
  AND ltv IS NOT NULL AND dti_band <> '9 Missing' AND conforming IS NOT NULL
  AND county_fips IS NOT NULL AND state_code IS NOT NULL;
