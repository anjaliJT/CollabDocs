# CollabDocs

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your local environment file from the example:

```bash
cp .env.example .env
```

4. Update `.env` with your local PostgreSQL credentials and database name.

## Apply Migrations

Run Django migrations to create the database tables:

```bash
python manage.py migrate
```

## Run the Server

Start the development server on port 8000:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Notes

- The app reads database settings from `.env`.
- If you change the database credentials, update `.env` before running migrations or the server.

## Demo Video

- Yogesh Jain: https://drive.google.com/file/d/13DcGqpcBfILdkHcfTaw9md6k3mfkEGi8/view?usp=sharing