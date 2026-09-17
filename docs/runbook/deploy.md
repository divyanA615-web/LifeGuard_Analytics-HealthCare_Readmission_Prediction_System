# Runbooks

## Deploy a new model version

```bash
cd ml
dvc repro                 # regenerate artefacts (data → train → evaluate)
# Upload model artefacts to the Render persistent disk or bake them into
# the image layer (see Dockerfile.render), then trigger a Render deploy:
git push origin main      # autoDeploy picks up the change
```

## Rotate the PHI encryption key

1. Generate a new 32-byte key: `openssl rand -base64 32`
2. Render Dashboard → `lifeguard-backend` → Environment → update `LOCAL_KEK`
3. Redeploy the service (Render restarts on env change)
4. Old ciphertexts must be re-encrypted or the old KEK kept in a keyset for rollback
5. Verify the audit log records the rotation

## Restore PostgreSQL backup

1. Render Dashboard → `lifeguard-db` → Backups
2. Choose a point-in-time snapshot → **Restore**
3. Render provisions a replacement instance and updates `DATABASE_URL`
   on the linked web service automatically
4. Verify `GET /v1/health` returns 200 after restore

## Investigate a prediction complaint

1. Pull audit entries for the patient:

   ```sql
   SELECT * FROM audit_entries
    WHERE payload_json->>'prediction_id' = '<id>'
    ORDER BY id ASC;
   ```
2. Verify chain integrity: `audit_chain.verify_chain()` from `audit_logger.py`
3. If chain is broken → alert security ops immediately

## Cost spike

1. Open Render Dashboard → Billing
2. Inspect the offending service (web ↔ PostgreSQL ↔ bandwidth)
3. Common causes: debug-level logging left on, NVIDIA free-tier limit
   exceeded forcing fallback retry loops, oversized Docker image pushes
