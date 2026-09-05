# 📦 Archived Legacy Code

This folder preserves the original 2020 Coding Dojo bootcamp version of the
project (Flask + raw PyMySQL, single `server.py`). It is kept for historical
reference only — **do not run or deploy anything in here.**

## ⚠️ Known security issues in the archived code

Why it was archived (all of these are fixed in the current app at the repo root):

- 🔑 Hardcoded Flask `SECRET_KEY` (`"Blahzay Blahzay"`) and `debug=True`
- 🗄️ Hardcoded MySQL `root`/`root` credentials in `mysqlconnection.py`
- 🗺️ A real Google Maps API key committed in `legacy_templates/contact.html`
  — **verified still ACTIVE on 2026-09-05** (serves Maps Embed requests with
  HTTP 200; Geocoding/Static are not enabled on its project, and its project
  has billing disabled). **Revoke/delete this key in the Google Cloud
  Console** — removing it from the repo does not un-leak it (it remains in
  git history and has been public since 2020).
- 🥶 Per-user Fernet encryption keys stored in plaintext in the `keys` table
- 🚪 Most routes had no login check (IDOR), and delete/follow actions used
  GET requests with no CSRF protection
- 📤 Avatar uploads checked only the file extension

## ⚠️ Sensitive data in the SQL dumps

`chad_ivan_daniel_group_project_data.sql` contains real (old) bcrypt password
hashes, Fernet keys, and encrypted messages for seed users. Treat them as
breached credentials:

- Never reuse those passwords anywhere.
- If any account (email + password combo) is still used in real life,
  change that password.

The dumps are kept only as a data-migration reference.
