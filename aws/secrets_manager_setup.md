# AWS Secrets Manager setup

Store the JDBC source credential once, read it everywhere (Lambda, Matillion),
never hardcode it.

```bash
aws secretsmanager create-secret \
  --name oncolake/jdbc-source \
  --secret-string '{"user":"oncolake_ro","password":"<pw>","host":"<host>","port":"5432","db":"source"}'
```

Read it in code (see aws/lambda/validate_and_alert.py -> get_secret).
In Matillion, add a "Secrets Manager" credential and reference it in the
database query component instead of typing the password.

Cost: about 0.40 USD per secret per month, with a 30-day free trial per
secret. Delete it when the project is done:

```bash
aws secretsmanager delete-secret --secret-id oncolake/jdbc-source --force-delete-without-recovery
```
