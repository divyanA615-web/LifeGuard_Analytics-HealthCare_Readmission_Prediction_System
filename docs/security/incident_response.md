# Incident Response Playbook

## Severity classification

| Severity | Definition | Response time |
|----------|-----------|---------------|
| SEV1 | Full outage, PHI leak suspected | < 30 min |
| SEV2 | Partial service degradation | < 4 hours |
| SEV3 | Single user impact | < 1 business day |

## SEV1: PHI leak suspected

1. **Freeze**: revoke the API service account token in IAM
   ```bash
   gcloud iam service-accounts keys list \
     --iam-account=lifeguard-api-prod@project-b0677df0-7b67-4302-a4a.iam.gserviceaccount.com
   gcloud iam service-accounts keys delete <KEY_ID>
   ```
2. **Investigate**: search audit log for the relevant record
3. **Notify**: Slack `#security-incidents` + HIPAA privacy officer (email)
4. **Document**: open an issue, capture findings in `incidents/<date>-<slug>.md`

## SEV2: Service degradation

1. Check Cloud Run metrics → status page
2. If CPU saturation: scale `max-scale` annotation via Terraform
3. If model drift: roll back to previous model revision via MLflow
4. If Cloud SQL: check connections, restart if needed

## Audit Chain Compromise

1. Run `verify_chain()` from `audit_logger.py`
2. If chain broken → immediately freeze writes
3. Restore chain from the most recent cloud backup
4. Investigate clock drift or attempted tamper

## Rotation emergency

1. Force-rotate the PHI key (Cloud KMS UI) outside of normal cadence
2. Confirm Cloud Run services pick up the new key on next cold start
3. Update the runbook with the rotation ID for audit purposes

## Contacts

* Platform on-call: #lifeguard-oncall
* HIPAA privacy officer: privacy@lifeguard.local
* GCP support: GCP console → support tickets premium package
