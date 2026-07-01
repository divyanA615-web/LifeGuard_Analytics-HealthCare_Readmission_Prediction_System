# Contributing to LifeGuard Readmission

Thank you for your interest! This repository is a private proof-of-concept.
The exact collaboration model (open-source / BAA‑only) will be decided when
the first healthcare-counterparty onboarding happens.

## How to participate

1. **Open an issue** describing the bug, idea, or feature request.
2. **Forks** are not currently accepted. Open an Issue and a maintainer
   will triage.
3. **Pull requests** are accepted from named collaborators only on
   `main`. PRs landing on `main` require:
   * tests passing in CI
   * sign-off (DCO line `Signed-off-by:`)
   * a maintainer review

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r ml/requirements.txt -r backend/requirements.txt
python ml/data/download_dataset.py --force-synthetic
python ml/run_all.py
cd frontend && npm install && npm run dev
```

## Style

* Python: black + isort + ruff
* TypeScript: prettier + eslint (default Vite plugin)
* Terraform: `terraform fmt -check -recursive`

## Commit messaging

Use Conventional Commits:

```
feat: add SHAP-related feature importance
fix: detect NaN in payer code
docs: rewrite encryption layer description
refactor: separate pipeline assembly from inference
test: add AAD protection tests
chore: bump skl2onnx pin
```

## Security

If you find a vulnerability, **do not file a public issue**. Follow the
process in `SECURITY.md`.

## License

By submitting a contribution, you agree that your contribution may be
licensed under the project's Apache-2.0 license, with the perpetual
right for the maintainer to re-license at their discretion (required
for BAA/medical integrations).
