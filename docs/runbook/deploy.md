# Runbooks

## Deploy a new model version

```bash
cd ml
dvc repro                 # regenerate artefacts (data → train → evaluate)
gcloud auth application-default login
gsutil cp -r ml/models/xgboost_v2 gs://lifeguard-models-prod/
# Update Cloud Run image tag, then promote via Cloud Deploy
```

## Rotate the PHI encryption key

1. Cloud Console → Key Management → select the PHI key ring
2. **Rotate** → set rotation period to 90 days
3. Cloud Run apps will use the new key on next cold start
4. Existing ciphertexts remain decryptable thanks to key versioning
5. Verify the audit log records the rotation

## Restore Cloud SQL backup

```bash
gcloud sql backups list --instance=dev-lifeguard-pg
gcloud sql backups restore <BACKUP_ID> \
    --backup-instance=dev-lifeguard-pg \
    --target-instance=dev-lifeguard-pg-restored
```

## Investigate a prediction complaint

1. Pull audit entries for the patient:

   ```sql
   SELECT * FROM audit_entries
    WHERE payload_json->>'prediction_id' = '<id>'
    ORDER BY id ASC;
   ```
2. Verify chain integrity: `audit_chain.verify_chain()` from `audit_logger.py`
3. If chain is broken → alert security ops immediately
4. Pull the prediction PHI from KMS via the emergency-decryption runbook only

## Cost spike

1. Open Cloud Console → Billing → Budgets & Alerts
2. Inspect the offending SKU (Cloud SQL ↔ Cloud Run ↔ Cloud NAT)
3. Common causes: runaway GKE node pool (disable via `cloudrun.command`), unexpected Pub/Sub fanout, debug-level logging left on
