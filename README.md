# 🤫 Whisper

> Share encrypted whispers with the people you follow.
> A modernized, security-hardened rewrite of a 2020 Coding Dojo group project.

[![CI](https://github.com/Coding-Dojo-PnA-Jan2020/chad_ivan_daniel_group_project/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)
![Flask](https://img.shields.io/badge/flask-3.x-green)
![License](https://img.shields.io/badge/license-unlicense-lightgrey)
![Security](https://img.shields.io/badge/pip--audit-clean-brightgreen)

---

## ✨ What is Whisper?

Whisper is a tiny Twitter-style social network:

| Feature | Description |
|---|---|
| 🔐 **Encrypted whispers** | Every post is encrypted with a **per-user Fernet key derived at runtime** — ciphertext is all the database ever sees |
| 🥷 **Follow ninjas** | Your feed shows whispers from you and the people you follow |
| ❤️ **Likes** | One like per person per whisper (enforced by the database) |
| 👤 **Profiles** | Bio editing and avatars with **generated defaults** — uploads are optional |
| 🔑 **Password reset** | Signed, expiring tokens (1 hour) via `itsdangerous` |
| 🛡️ **Hardened by default** | CSRF on every form, rate-limited login/register, strict upload validation |

## 🚀 Quickstart

```bash
# 1 — clone & enter
git clone https://github.com/Coding-Dojo-PnA-Jan2020/chad_ivan_daniel_group_project.git
cd chad_ivan_daniel_group_project

# 2 — create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows Git Bash: source .venv/Scripts/activate

# 3 — install
pip install -r requirements.txt

# 4 — (optional) configure — a random dev key and SQLite are used if you skip this
cp .env.example .env

# 5 — run
flask --app wsgi run
```

Open **http://127.0.0.1:5000** 🎉 — register an account and start whispering.
No database setup needed for local play: the app defaults to a local SQLite file.

### 🐬 Using MySQL instead

```bash
# create a database + user, then:
export DATABASE_URL="mysql+pymysql://whisper:password@localhost:3306/whisper"
flask --app wsgi db upgrade     # create the schema via migrations
```

## ⚙️ Configuration

All configuration comes from the environment (or a `.env` file — see
[`.env.example`](.env.example)). **No secrets are ever committed.**

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | ✅ in production | random per process | Session signing **and** the root of the whisper-encryption key hierarchy |
| `DATABASE_URL` | ❌ | `sqlite:///whisper_local.db` | SQLAlchemy URL (`mysql+pymysql://…` for MySQL) |
| `FLASK_CONFIG` | ❌ | `development` | `development` / `testing` / `production` |
| `AVATAR_STYLE` | ❌ | `adventurer` | [DiceBear](https://www.dicebear.com) style for generated avatars |
| `RATELIMIT_STORAGE_URI` | ❌ | `memory://` | e.g. `redis://…` when running multiple instances |

> ⚠️ **Production:** set `FLASK_CONFIG=production` and `SECRET_KEY`.
> The app **refuses to start** in production mode without a real `SECRET_KEY`.

## 🏗️ Project layout

```
├── app/
│   ├── __init__.py      # 🏭 app factory, extensions, error handlers
│   ├── config.py        # ⚙️ dev / test / prod configs (env-driven)
│   ├── crypto.py        # 🔐 HKDF → per-user Fernet keys (never stored)
│   ├── models.py        # 🗃️ SQLAlchemy: User, Whisper, Follow, Like
│   ├── forms.py         # 📝 WTForms with validation
│   ├── auth.py          # 👤 register / login / logout / password reset
│   ├── whispers.py      # 🤫 feed, create, delete, like
│   ├── users.py         # 🥷 profiles, follows, bio, avatar upload
│   ├── templates/       # 🎨 Jinja2 + Bootstrap 5
│   └── static/
├── migrations/          # 🧬 Alembic migrations (flask db …)
├── tests/               # ✅ pytest suite (36 tests)
├── archive/             # 📦 the original 2020 bootcamp code (do not run!)
├── .github/workflows/   # 🤖 CI: lint + tests + dependency audit
└── wsgi.py              # 🚪 entry point
```

## 🔐 Security architecture

### Whisper encryption

```
SECRET_KEY (server env, never in DB)
    └── HKDF-SHA256(info="whisper-message-key-v1:<user_id>")
            └── per-user Fernet key → encrypts that user's whispers
```

- **Keys are never stored.** A stolen database alone cannot decrypt whispers —
  the attacker needs `SECRET_KEY` too. (This replaces the legacy design that
  stored per-user keys in a plaintext `keys` table.)
- Whispers are **only decrypted in memory** while rendering your feed.
- `SECRET_KEY` rotation invalidates existing ciphertexts (they are skipped in
  the feed rather than crashing) — re-encrypt from a backup if needed.

### Everything else

- 🧱 **CSRF** — all state-changing routes are POST-only with Flask-WTF tokens
- 🚦 **Rate limiting** — login `20/hour`, register & reset `10/hour` per IP
- 🍪 **Session cookies** — `HttpOnly`, `SameSite=Lax`, `Secure` in production
- 🖼️ **Uploads** — magic-byte sniffing + full image re-encode via Pillow,
  random filenames, 2 MB request cap; **default avatars mean no upload at all**
- 🙈 **No user enumeration** — login and password-reset give identical
  responses whether or not the email exists
- 🔎 **No secrets in logs** — the old app printed keys and queries to stdout;
  this one never does

## 🛡️ Keeping it that way (no whack-a-mole)

Dependabot alerts used to pile up because this repo pinned 29 packages from
2020, mixing linters and unused libraries. The rewrite fixes the *process*:

1. **Minimal dependency surface** — 15 direct runtime packages, each one
   load-bearing. Fewer packages ⇒ fewer alerts.
2. **CI gate** ([ci.yml](.github/workflows/ci.yml)) — every push runs
   `ruff` + `pytest` + **`pip-audit`**, and the build *fails* on any known
   CVE before it can be merged. Alerts are caught pre-merge, not discovered
   post-deploy.
3. **Dependabot, de-noised** ([dependabot.yml](.github/dependabot.yml)) —
   weekly grouped minor/patch PRs (one reviewable PR instead of 15 alerts);
   major bumps still arrive individually.

So the maintenance loop is: Dependabot opens a grouped PR → CI validates it →
merge. Done. 🧹

### Running the checks yourself

```bash
pip install -r requirements-dev.txt
ruff check app tests wsgi.py
pytest -q
pip-audit -r requirements.txt -r requirements-dev.txt
```

## 🧪 Tests

36 pytest tests cover the security-critical paths:

- crypto round-trips, per-user key isolation, garbage-token handling
- register/login/logout, duplicate email, weak password, reset-token expiry
- unauthenticated access blocked on every page; cross-user deletes → 403
- feed visibility (only self + followed), CSRF enforcement, like uniqueness
- avatar upload: valid PNG, non-image rejection, size cap

## 🤝 Contributing

1. Branch from `master`
2. `ruff check` + `pytest` must pass (CI enforces this)
3. Add tests for any security-relevant change
4. Open a PR — Dependabot handles dependency bumps automatically

## 📜 History & credits

This started life as a January-2020 [Coding Dojo](https://www.codingdojo.com)
group project (Flask + raw PyMySQL). That original code lives in
[`archive/`](archive/) — preserved, explained, and **not to be run** (it
contains a committed API key and hardcoded credentials; the Google Maps key
was revoked during the rewrite). The current app is a ground-up rewrite.
