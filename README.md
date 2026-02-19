# Casting Agency API (FSND Capstone)

A Flask REST API for managing **Actors** and **Movies** with Auth0 authentication and role-based access control (RBAC).

## Motivation

This project models a casting agency workflow where different staff roles have different levels of access to actor and movie resources.

## Tech Stack

- Python
- Flask
- SQLAlchemy
- Flask-Migrate (Alembic)
- PostgreSQL
- Auth0 (JWT + RBAC)

## Live API

- Base URL: `https://<YOUR-DEPLOYED-URL>`

Replace with your real deployed URL before submission.

## Roles and Permissions

### Permissions (Scopes)

- `get:actors`, `get:movies`
- `post:actors`, `patch:actors`, `delete:actors`
- `post:movies`, `patch:movies`, `delete:movies`

### Roles

- Casting Assistant
- `get:actors`, `get:movies`

- Casting Director
- All Casting Assistant permissions, plus:
- `post:actors`, `patch:actors`, `delete:actors`
- `patch:movies`

- Executive Producer
- All Casting Director permissions, plus:
- `post:movies`, `delete:movies`

## API Endpoints

All protected endpoints require:

`Authorization: Bearer <ACCESS_TOKEN>`

### Actors

- `GET /actors` (requires `get:actors`)
- `POST /actors` (requires `post:actors`)
- `PATCH /actors/<id>` (requires `patch:actors`)
- `DELETE /actors/<id>` (requires `delete:actors`)

### Movies

- `GET /movies` (requires `get:movies`)
- `POST /movies` (requires `post:movies`)
- `PATCH /movies/<id>` (requires `patch:movies`)
- `DELETE /movies/<id>` (requires `delete:movies`)

### Health

- `GET /` (public)

## Local Setup

### 1. Clone and create virtual environment

```bash
python -m venv venv
```

Activate:

- Git Bash:
```bash
source venv/Scripts/activate
```

- PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Edit `setup.sh` and set your values.

```bash
source setup.sh
```

PowerShell equivalent:

```powershell
$env:DATABASE_URL="postgresql://postgres:<password>@localhost:5432/casting_agency"
$env:AUTH0_DOMAIN="<your-tenant>.eu.auth0.com"
$env:API_AUDIENCE="casting-agency"
$env:ALGORITHMS="RS256"
$env:ASSISTANT_TOKEN="<assistant_jwt>"
$env:DIRECTOR_TOKEN="<director_jwt>"
$env:PRODUCER_TOKEN="<producer_jwt>"
```

### 4. Create database and run migrations

```bash
createdb casting_agency
flask --app manage.py db init
flask --app manage.py db migrate -m "initial"
flask --app manage.py db upgrade
```

### 5. Run the app

```bash
python app.py
```

## Auth0 Setup

### 1. Create API

- Name: `Casting Agency API` (any name is fine)
- Identifier: `casting-agency`
- Enable:
- RBAC
- Add Permissions in the Access Token

### 2. Create permissions

- `get:actors`, `get:movies`
- `post:actors`, `patch:actors`, `delete:actors`
- `post:movies`, `patch:movies`, `delete:movies`

### 3. Create roles and assign permissions

- Casting Assistant: `get:actors`, `get:movies`
- Casting Director: assistant perms + actor create/update/delete + `patch:movies`
- Executive Producer: director perms + `post:movies`, `delete:movies`

### 4. Create users and assign one role to each user

- Assistant user -> Casting Assistant
- Director user -> Casting Director
- Producer user -> Executive Producer

### 5. Generate role-specific tokens

Use Auth0 `/oauth/token` (password-realm flow) per user:

```bash
curl --request POST \
  --url https://<YOUR_AUTH0_DOMAIN>/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "grant_type":"http://auth0.com/oauth/grant-type/password-realm",
    "username":"<user_email>",
    "password":"<user_password>",
    "audience":"casting-agency",
    "scope":"openid profile email",
    "client_id":"<YOUR_CLIENT_ID>",
    "client_secret":"<YOUR_CLIENT_SECRET>",
    "realm":"Username-Password-Authentication"
  }'
```

Copy `access_token` into:

- `ASSISTANT_TOKEN`
- `DIRECTOR_TOKEN`
- `PRODUCER_TOKEN`

## Testing

Run:

```bash
source setup.sh
python -m unittest -v
```

Current expected result:

- `Ran 21 tests ... OK`

## Example Requests

```bash
curl -H "Authorization: Bearer <ASSISTANT_TOKEN>" \
  http://127.0.0.1:5000/actors
```

```bash
curl -X POST http://127.0.0.1:5000/movies \
  -H "Authorization: Bearer <PRODUCER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Dune","release_date":"2021-10-22"}'
```

## Deployment Notes

- Configure env vars on your cloud platform (do not use local `setup.sh` in production).
- Run migration on hosted environment.
- Update this README with your final deployed URL.

## Security Notes

- Do not commit real JWTs or client secrets.
- Rotate any leaked Auth0 client secrets immediately.
- This project validates RS256 JWTs using Auth0 JWKS.
