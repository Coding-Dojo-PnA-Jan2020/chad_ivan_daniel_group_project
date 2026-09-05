# 🔒 Security Policy

## 📣 Reporting a vulnerability

Please **do not open a public GitHub issue** for security problems.

Instead, use GitHub's private vulnerability reporting:
**Security tab → Report a vulnerability**, or contact the repository owner
directly.

You can expect a response within **7 days**. Please include:

- a description of the issue and its impact
- steps to reproduce (or a proof of concept)
- affected routes/versions if known

## 🛡️ Security measures in this project

| Layer | Measure |
|---|---|
| Secrets | Environment-only (`SECRET_KEY`, `DATABASE_URL`); production refuses to boot without a real key |
| Passwords | Werkzeug password hashing (scrypt/PBKDF2), 8–128 char policy, hashes never logged |
| Sessions | `HttpOnly` + `SameSite=Lax` cookies, `Secure` in production, 8-hour lifetime |
| CSRF | Flask-WTF token on every state-changing POST |
| Rate limits | login 20/h, register 10/h, password reset 10/h per IP |
| Encryption | Per-user Fernet keys derived via HKDF from `SECRET_KEY` — never stored in the database |
| Uploads | Magic-byte + full decode validation, Pillow re-encode, random names, 2 MB cap, optional by design |
| Access control | `@login_required` everywhere private; ownership checks server-side (403 not 404) |
| Dependencies | Minimal pin list, `pip-audit` gate in CI, grouped weekly Dependabot updates |
| Containers | Multi-stage Dockerfile, non-root user, Trivy image + filesystem + misconfig scans gate CI; container smoke-tested on every PR |

## 🔁 Secret rotation

Rotating `SECRET_KEY` invalidates:

- all existing sessions (everyone is logged out), and
- all encrypted whispers (their per-user keys can no longer be derived —
  undecryptable whispers are skipped in the feed, not shown as errors).

If you need to rotate and preserve whispers, decrypt them with the old key
(`app.crypto.decrypt_message`) and re-encrypt with the new key
(`app.crypto.encrypt_message`) from a one-off script **before** switching.

## 🧰 Supported versions

Only the latest `master` is supported. Dependabot + CI keep it patched —
merge the grouped dependency PRs weekly and you're done.
