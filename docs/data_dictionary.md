# Data dictionary

## `applications` (DuckDB, one row per decided application; `sql/02_applications.sql`)

| Column | Type | Source field | Meaning |
|---|---|---|---|
| app_id | integer | row number | surrogate key (the public file has no application ID) |
| lei | text | lei | lender legal entity identifier |
| state_code, county_fips, census_tract | text | state_code, county_code, census_tract | property location (NULL when not reported) |
| msa_md | text | derived_msa-md | metropolitan area (99999 = outside an MSA) |
| action_taken | integer | action_taken | 1 originated, 2 approved not accepted, 3 denied |
| approved, denied, originated | integer 0/1 | action_taken | outcome flags |
| loan_type | text | loan_type | Conventional, FHA, VA, USDA |
| core | boolean | several | first lien, principal residence, site-built 1-4 units, not business purpose, not reverse, not open-end |
| applicant_group | text | derived_ethnicity, derived_race | White, Black, Hispanic, Asian, Other minority, Joint, Not reported (see methodology) |
| sex | text | derived_sex | Male, Female, Joint, Not reported |
| age_band | text | applicant_age | HMDA age band; 8888 shown as Not reported |
| income_k | double | income | gross annual income relied on, $ thousands (NULL if missing or not positive) |
| loan_amount | double | loan_amount | $, midpoint of the $10,000 bin |
| property_value | double | property_value | $, midpoint of the $10,000 bin |
| ltv | double | loan_to_value_ratio | combined loan-to-value, % (NULL outside 1-250) |
| dti_raw, dti_exact | text, integer | debt_to_income_ratio | as published; exact value for 36-49 |
| dti_band | text | debt_to_income_ratio | 1 <20%, 2 20-29%, 3 30-35%, 4 36-39%, 5 40-44%, 6 45-49%, 7 50-60%, 8 >60%, 9 Missing |
| dti_value | integer | debt_to_income_ratio | plotting value: exact 36-49, band midpoints otherwise |
| ltv_band | text | ltv | 1 <=60%, 2 60-80%, 3 80-90%, 4 90-95%, 5 95-97%, 6 >97%, 7 Missing |
| income_band | text | income, ffiec_msa_md_median_family_income | applicant income as % of area median: Low, Moderate, Middle, Upper, Missing |
| interest_rate, rate_spread | double | interest_rate, rate_spread | note rate %, APR minus average prime offer rate (percentage points) |
| total_loan_costs, discount_points | double | same | $ |
| loan_term | integer | loan_term | months |
| fixed_amortizing | boolean | intro_rate_period and features | fixed rate with no balloon, interest-only, negative amortization or other non-amortizing feature |
| conforming | integer 0/1 | conforming_loan_limit | 1 = within the conforming loan limit |
| preapproval | integer 0/1 | preapproval | preapproval requested (not used as a control) |
| direct_application | integer 0/1 | submission_of_application | submitted directly to the lender |
| credit_model, aus | text | applicant_credit_score_type, aus-1 | credit scoring model and automated underwriting system codes |
| denial_reason_1..4 | integer | denial_reason-1..4 | 1 DTI, 2 employment history, 3 credit history, 4 collateral, 5 insufficient cash, 6 unverifiable information, 7 incomplete application, 8 mortgage insurance denied, 9 other, 10 not applicable |
| tract_minority_pct, tract_income_pct | double | tract fields | minority share of tract population; tract median family income as % of area median |
| tract_minority_band, tract_income_band | text | tract fields | banded versions |
| area_median_income | double | ffiec_msa_md_median_family_income | FFIEC area median family income, $ |

Views: `core` (core sample) and `model_frame` (core, five compared groups, every control present).

## Report tables (`reports/tables/`)

| File | Grain | Notes |
|---|---|---|
| rates_by_group.csv | applicant group | applications, approval and denial rates, Wilson interval, approval AIR, denial-rate ratio, shares with DTI 50%+ and LTV over 95% |
| denial_gap_ladder.csv | specification x group | LPM coefficient (share points), standard error clustered by lender and 95% CI |
| logit_marginal_effects.csv | group | average marginal effect, delta-method CI, odds ratio |
| oaxaca_blinder.csv | group | raw gap, explained, unexplained (with CI) and block contributions |
| pricing_gaps.csv | specification x group | rate-spread gap in basis points |
| neighbourhood_gaps.csv | tract minority band | raw rate and adjusted difference against tracts under 10% minority |
| lender_screen.csv | lender | raw and adjusted Black and Hispanic gaps with CIs, screen flag |
| denial_by_dti.csv | loan type x DTI value | applications, denial rate, share of denials citing DTI |
| denial_reasons.csv | group x reason | share of denied applications citing the reason |
| policy_grid.csv | group x DTI band x LTV band | applications, approvals, denials, approved volume (Excel input) |
| policy_scenarios.csv | scenario x group | approvals and AIR before and after a cap |
| lender_benchmark_top_200.csv, states.csv, counties.csv, tracts.csv | lender, state, county, tract bands | descriptive views |

## Power BI extracts (`dashboards/powerbi/data/`)
`fact_applications.csv` (state x loan type x group x DTI band x LTV band with applications, approved, denied,
originated and originated volume), `income_tract.csv`, `dti_profile.csv`, `denial_reasons.csv`,
`gap_ladder.csv` (percentage points), `pricing_gaps.csv` (basis points), `lender_screen.csv` (gaps in
percentage points), `county_rates.csv`, `dim_group.csv`.
