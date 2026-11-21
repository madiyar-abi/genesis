FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535 AS runtime

FROM runtime AS policy
WORKDIR /policy
COPY auditenv/__init__.py auditenv/schema.py auditenv/money.py auditenv/tool_spec.py auditenv/policy_worker.py ./auditenv/
COPY auditenv/policies/__init__.py auditenv/policies/flag_all.py auditenv/policies/random_explorer.py auditenv/policies/reconcile.py ./auditenv/policies/
USER 65534:65534
ENTRYPOINT ["python", "-B", "-m", "auditenv.policy_worker"]

FROM runtime AS grader
WORKDIR /app
COPY . .

CMD ["python", "-m", "auditenv.check"]
