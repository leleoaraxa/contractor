# Stage 3 / ADR 0028 / Rollback — Evidência (non-prod)

**Escopo:** evidência operacional em ambiente compose/local (não produção).

**Referências:** ADR 0028; `docs/RUNBOOKS/rollback.md`; `scripts/dev/smoke.sh`.

## Commands executed

```bash
docker compose exec runtime bash -lc "./scripts/dev/smoke.sh"
```

## Observed output

```text
[+] Check control healthz...
[+] Check runtime healthz...
[+] Run quality report for tenant=demo bundle=202601050001
[+] Quality status=pass suites=['data/quality/suites/demo_routing_candidate_suite.json', 'data/quality/suites/demo_thresholds_suite.json']
[+] Set candidate alias (gate enforced)...
[+] Promote candidate -> current (gate enforced)...
[✓] Promotion succeeded.
[+] Rollback current to previous value...
Promotion PASS (bundle 202601050001)...
Promotion PASS OK
Promotion FAIL (template safety, bundle 202601050002)...
Template safety gate OK
Rate limit enforcement (bundle 202601050003)...
Rate limit OK
Smoke test completed
```

## What this proves

- healthz control/runtime OK.
- quality gate OK.
- candidate -> current OK.
- rollback to previous OK (bundle 202601050001).
- template safety gate blocks unsafe bundle (202601050002).
- rate limit enforcement OK (202601050003).

## What this does NOT prove

- NÃO é produção.
- NÃO fecha o item “Rollback completo validado em produção”.
- NÃO há evidência de logs/telemetria de produção.

## Conclusion

Rollback validated (non-prod) = SIM; Rollback validated (production) = NÃO.
