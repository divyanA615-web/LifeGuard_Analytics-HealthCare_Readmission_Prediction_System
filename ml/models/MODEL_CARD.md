# 🏥 Readmission Prediction — Model Card

## Overview

| Field | Value |
|-------|-------|
| Model | XGBoost Classifier (CPU-runnable ONNX export) |
| Task | 30-day hospital readmission prediction |
| Audience | Clinicians, case managers, discharge planners |
| Owner | LifeGuard Analytics |
| Version | v1.0 |
| Date | 2026-06-30 |
| License | Apache 2.0 |

## Intended Use

✅ **Intended for:**
- Triage support during discharge planning
- Population health dashboards
- Quality-improvement programs

❌ **NOT intended for:**
- Standalone diagnostic decisions
- Clinical decisions without clinician review
- Treatment recommendations
- Use on populations outside U.S. diabetic readmissions

## Training Data

| Source | Size | Last Verified |
|--------|------|--------------|
| Diabetes 130-US Hospitals (UCI/Kaggle) | 101,766 encounters | 2026-06-30 |
| Synthea (synthetic FHIR) - optional augment | varies | — |
| MIMIC-IV - optional augment | ~500K admissions (ICU subset) | — |

> **Important:** The model was trained on U.S. diabetic hospital data 1999–2008.
> Performance may degrade on:
> - Different hospital systems
> - Non-diabetic populations
> - Non-U.S. patients
> - Post-COVID populations
> - Pediatric patients

## Features

Numeric (11): `age`, `time_in_hospital`, `num_lab_procedures`, `num_procedures`,
`num_medications`, `number_outpatient`, `number_emergency`, `number_inpatient`,
`number_diagnoses`, `max_glu_serum_num`, `a1c_result_num`

Categorical/Binary: `gender_male`, `admission_type_emergency`,
`discharge_to_home`, `payer_code`, `insulin_use`, `metformin_use`,
`diabetesMed_yes`, `change_in_meds`

> **No PHI fields used** — all features are derived from de-identified records.

## Metrics (Test Set)

| Metric | Value | Threshold |
|--------|------|-----------|
| AUC-ROC | (auto-filled from `ml/metrics/evaluation.json`) | ≥ 0.80 |
| AUC-PR | (auto) | ≥ 0.35 |
| F1 Score | (auto) | ≥ 0.45 |
| Brier Score | (auto) | ≤ 0.20 |
| Calibration Error | (auto) | ≤ 0.05 |

## Fairness Audit

Metrics across gender (binary gender_male flag):

| Slice | AUC-ROC | AUC-PR | Count |
|-------|---------|--------|-------|
| Female | (auto) | (auto) | (auto) |
| Male | (auto) | (auto) | (auto) |

Demographic parity difference should remain < 0.10.

## Limitations & Risks

- **Selection bias:** diabetes-only population
- **Temporal shift:** training data may not match current practice
- **Coding drift:** ICD-9 used; current hospital systems use ICD-10
- **Concept drift:** efficacy of discharge interventions changes over time
- **Group fairness:** race/ethnicity equity metrics require demographic features
  not yet collected (see TODO)

## Compliance

- HIPAA: only used with de-identified data per U.S. public dataset license
- GDPR: additional consent workflow required for EU populations
- Plain-language summary reviewed by clinical pharmacists

## Ethics Review

- Conflict-of-interest: model developers free of clinical commercial ties ✓
- Data source license (CC0 / public benchmark) ✓
- Stakeholder consultation: planned before prod rollout

## References

- [Strack et al., 2014](https://www.hindawi.com/journals/bmri/2014/781670/)
- [Rajkomar et al., 2018](https://www.nature.com/articles/s41746-018-0029-1)
- [BEHRT & Med-BERT papers](https://arxiv.org/abs/1905.04794)
