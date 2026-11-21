# Methodology

## Data and scope
The 2025 HMDA modified loan application register, filtered by the Data Browser API to home-purchase applications
(loan purpose 1) that reached a credit decision: originated (action 1), approved but not accepted (2) or denied
(3). Withdrawn, incomplete and purchased loans and denied preapproval requests (actions 4 to 8) are not in the
file.

The **core sample** keeps first-lien loans for a principal residence on a site-built 1-4 unit home, not for a
business purpose, not reverse mortgages and not open-end lines of credit. Records from partially exempt
reporters (code 1111 on these fields) cannot be classified and are left out of the core sample. Every rule
and its row count is in `data_quality_log.md`.

**Outcomes.** Approved = action 1 or 2; denied = action 3. Rates are shares of decided applications.

**Applicant groups.** From HMDA's derived ethnicity and race fields, which already combine applicant and
co-applicant: Hispanic or Latino (any race); then, for non-Hispanic applicants, White, Black or African
American, Asian, and Other minority (American Indian or Alaska Native, Native Hawaiian or Other Pacific
Islander, two or more minority races). Applications whose derived ethnicity or race is "Joint" (applicant and
co-applicant in different groups) are shown as Joint; applications without race or ethnicity are "Not
reported". White applicants are the reference group in every comparison.

## Rates and ratios
* Wilson score intervals for denial rates.
* **Approval-rate adverse impact ratio (AIR)** = group approval rate / White approval rate, screened against
  0.80 (the four-fifths rule from the federal Uniform Guidelines on Employee Selection, used in lending as a rule
  of thumb, not a legal threshold).
* **Denial-rate ratio** = group denial rate / White denial rate. With approval rates around 90%, a large denial
  gap moves the approval AIR very little, so both are reported.

## Underwriting profile
`sql/06_dti_profile.sql` reports the denial rate at each published DTI value. HMDA gives DTI as exact integers
from 36% to 49% and in bands otherwise (<20%, 20-29%, 30-35%, 50-60%, >60%); bands are plotted at 15, 25, 33, 55
and 65. Fannie Mae's Selling Guide (B3-6-02) caps DTI at 50% for loans underwritten through Desktop Underwriter
and at 36% (45% with compensating factors) for manual underwriting. Denial reasons (up to four per application)
are unnested in `sql/07_denial_reasons.sql`; shares are of denied applications citing each reason.

## Denial gap ladder
Linear probability model on the **model frame**: core applications from the five compared groups with every
control present (income, loan amount, property value, LTV between 1% and 250%, a reported DTI, conforming flag,
county and state).

denied = group indicators (Black, Hispanic, Asian, Other minority; White omitted) + controls + fixed effects + error

1. Raw: group indicators only.
2. Underwriting controls: DTI band (8 bands, 30-35% omitted), LTV band (6 bands, 60-80% omitted), log income,
   log loan amount, log property value, conforming-loan-limit flag, loan type (FHA, VA, USDA; conventional
   omitted), age band, sex (including joint), direct application to the lender, census-tract income band.
3. Plus lender x state fixed effects.
4. Plus lender x county fixed effects: applicants compared with others at the same lender in the same county.

Fixed effects are absorbed exactly by subtracting group means (one combined key per specification; singleton
groups dropped). Standard errors are clustered by lender (CR1), with t critical values on G - 1 degrees of
freedom. Coefficients are percentage-point differences in denial probability. The preapproval flag is not a
control: denied preapproval requests are reported under action 7, so applications with a preapproval request
in this file are never denied (the flag predicts approval perfectly by construction).

**Logit check.** Logit with the specification 2 controls and state indicators (states with fewer than 500
sampled applications pooled) on a 600,000-row random sample. The average marginal effect of group g is the mean
over sampled applicants of P(deny | g, x) - P(deny | White, x), with x at each applicant's own values; the 95%
interval uses the delta method on the logit covariance matrix.

## Oaxaca-Blinder decomposition
For each group against White applicants, OLS on the two groups pooled with the specification 2 controls and a
group indicator (the pooled decomposition of Fortin, 2008, and Jann, 2008). Explained part = sum over controls of
(mean of the control for the group - mean for White applicants) x pooled coefficient; unexplained part = the
coefficient on the group indicator. Because the regression has an intercept and the group indicator, residuals
average zero within each group and explained + unexplained equals the raw gap exactly (checked in the tests).
Contributions are summed into blocks: debt-to-income, loan-to-value, income and loan size, loan type, age and
sex, neighbourhood income, application channel.

## Pricing
Originated conventional loans with a 30-year term, fixed rate, fully amortizing (no intro period, balloon,
interest-only or negative amortization), with a reported rate spread between -5 and 10 percentage points. The
rate spread is the APR minus the average prime offer rate for a comparable loan on the rate-lock date, so market
moves are already netted out. Outcome in basis points; controls as in specification 2 plus discount points as a
percentage of the loan amount (points buy the rate down). Specifications: raw, controls, controls plus lender x
state fixed effects; errors clustered by lender.

## Neighbourhoods
Specification 3 plus census-tract minority-share bands (<10% omitted). The coefficients measure whether
applications in high-minority tracts are denied more often than comparable applications from the same lender
in the same state, after the applicant's own group and controls.

## Lender screen
Lenders with at least 5,000 applications in the model frame and at least 300 Black and 300 Hispanic applicants.
For each, the specification 2 regression on its own applications with county fixed effects and errors clustered
by county. A lender is marked "Gap above zero: review files" when the lower end of the 95% interval for the
Black or the Hispanic gap is above zero. This is the step that selects files for a matched-pair review; it is not
a conclusion about the lender.

## Policy simulator
The Excel workbook and `fairlending.simulate_policy` use the core-sample grid of group x DTI band x LTV band.
A cap turns away the approved applications in bands above it; denied applications stay denied. Applications with
DTI or LTV not reported pass the cap by default (an input). Approval rates, AIRs, approvals and approved loan
volume lost are recomputed; revenue lost = volume lost x the revenue rate input (an assumption).

## Limits
* No credit score, assets, reserves or employment detail in the public data, and DTI is banded outside 36-49%.
  Credit history is the reason cited most often after DTI, and more often for Black applicants, so part of the
  remaining gap may reflect credit differences the data cannot show.
* The model frame drops applications missing a control. They are denied more often, so the regression sample
  understates the overall denial rate.
* HMDA has no application or lock dates, so neither the timing of applications nor rate locks can be modelled.
* Applicant group is self-reported or collected by visual observation for some applications, as HMDA requires.
