# Incident Response Playbook

## Severity classification

| Severity | Definition | Response time |
|----------|-----------|---------------|
| SEV1 | Full outage, PHI leak suspected | < 30 min |
| SEV2 | Partial service degradation | < 4 hours |
| SEV3 | Single user impact | < 1 business day |

## SEV1: PHI leak suspected

1. **Freeze**: rotate the compromised credential immediately
   * Render Dashboard → `lifeguard-backend` → Environment → regenerate
     `DEV_AUTH_TOKEN` / `LOCAL_KEK` → redeploy
   * Vercel Dashboard → project → Settings → Environment Variables →
     rotate any frontend tokens → redeploy
2. **Investigate**: search audit log for the relevant record
3. **Notify**: Slack `#security-incidents` + HIPAA privacy officer (email)
4. **Document**: open an issue, capture findings in `incidents/<date>-<slug>.md`

## SEV2: Service degradation

1. Check Render Dashboard → service metrics + logs → status page
2. If CPU saturation: upgrade the Render plan (starter → standard)
3. If model drift: roll back to previous model revision via MLflow
4. If PostgreSQL: check connection count, restart instance if needed

## Audit Chain Compromise

1. Run `verify_chain()` from `audit_logger.py`
2. If chain broken → immediately freeze writes
3. Restore chain from the most recent Render PostgreSQL backup
4. Investigate clock drift or attempted tamper

## Rotation emergency

1. Rotate `LOCAL_KEK` outside of normal cadence (see runbook)
2. Confirm the Render service picks up the new key after redeploy
3. Update the runbook with the rotation ID for audit purposes

## Contacts

* Platform on-call: #lifeguard-oncall
* HIPAA privacy officer: privacy@lifeguard.local
* Render status: https://status.render.com
