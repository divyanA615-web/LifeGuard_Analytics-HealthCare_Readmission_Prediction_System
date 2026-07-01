# Pull Request template — LifeGuard Readmission

## What does this PR change?

<!-- Required: 1-line summary + 1-paragraph description of the change. -->

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Related ticket / issue

- Link to relevant issue: <!-- e.g. #14 -->

## How was this tested?

- [ ] Tests updated
- [ ] New tests added
- [ ] Manual verification steps captured below

## Compliance & privacy checklist

<!-- Most PRs in healthcare need this. If your change touches PHI, do NOT push. -->

- [ ] No PHI, real patient identifiers, or production credentials are included
- [ ] No change bypasses the de-identification gate (`backend/app/security/deid_gate.py`)
- [ ] No change weakens the encryption AAD binding
- [ ] Terraform changes still meet OPA guard rails (no public IPs, CMEK-only)
- [ ] CI pipeline passes (lint, tests, security scans)
- [ ] DCO sign-off included (commit body or PR comment)

## Documentation

- [ ] `README.md` / `docs/` updated when the user-visible surface changes
- [ ] Inline comments referencing new PHI/PII fields added where relevant

## Reviewer notes

<!-- Anything else. -->
