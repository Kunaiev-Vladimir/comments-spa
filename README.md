# Comments SPA

A single-page comments application developed as a Junior Python Developer test assignment for dZENcode.

The project supports nested comments, CAPTCHA validation, file attachments, sorting, pagination, HTML validation, and real-time updates using WebSocket.

## Live Demo

**Deployed application:** <https://comments-spa-c83f.onrender.com/>

The application is deployed on Render and uses Neon PostgreSQL for database storage and Cloudinary for persistent file attachments.

The deployed version supports comments, nested replies, CAPTCHA validation, file uploads, and real-time updates through WebSocket.

## Tech Stack

**Backend:** Python 3.14, Django 6.1, Django REST Framework, Django Channels, Daphne.

**Frontend:** Vue.js, Vite, HTML, CSS, JavaScript.

**Database:** PostgreSQL 18.

**Infrastructure:** Docker, Docker Compose, Nginx.

**Additional libraries:** Pillow, django-simple-captcha, defusedxml.

## Features

- Create comments with username, email, optional home page, text, and CAPTCHA.
- Reply to comments with recursive nesting.
- Sort top-level comments by username, email, and creation date in ascending or descending order.
- Display 25 top-level comments per page.
- Validate input on both the client and server.
- Support the allowed HTML tags: `<a>`, `<code>`, `<i>`, and `<strong>`.
- Attach JPG, JPEG, PNG, GIF, and TXT files.
- Resize oversized images proportionally to fit within 320 × 240 pixels.
- Limit TXT attachments to 100 KB.
- Preview comments before submitting.
- Receive real-time notifications of new comments through WebSocket.
- Display interface messages in Ukrainian, Russian, and English.

## Requirements

- Docker Desktop or Docker Engine
- Docker Compose
- Git

Python, Node.js, and PostgreSQL do not need to be installed separately when using Docker.

## Installation with Docker

### 1. Clone the repository

```bash
git clone https://github.com/Kunaiev-Vladimir/comments-spa.git
cd comments-spa
```

### 2. Create the environment configuration

Copy `.env.example` to `.env`.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

On Linux/macOS:

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholder values of `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD` with secure values.

Generate a Django secret key, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

If Python is not installed locally, generate the key using another trusted secure random generator.

Do not commit `.env` to Git.

### 3. Start the application

```bash
docker compose up -d --build
```

Docker Compose starts PostgreSQL, Django/Daphne, and Nginx.

The Django container automatically runs database migrations and collects static files.

### 4. Open the application

**Application:** <http://127.0.0.1:8000/>

**REST API:** <http://127.0.0.1:8000/api/comments/>

**CAPTCHA API:** <http://127.0.0.1:8000/api/comments/captcha/>

**Django Admin:** <http://127.0.0.1:8000/admin/>

**WebSocket:** ws://127.0.0.1:8000/ws/comments/

### 5. Check container status

```bash
docker compose ps
```

### 6. View logs

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 nginx
```

### 7. Stop the application

```bash
docker compose down
```

This command stops and removes containers while preserving named database volumes.

**Warning:** `docker compose down -v` also removes named volumes and may delete your database contents.

## Django Admin

To create an administrator:

```bash
docker compose exec web python manage.py createsuperuser
```

Then open:

<http://127.0.0.1:8000/admin/>

## REST API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/comments/` | List comments and nested replies |
| POST | `/api/comments/` | Create a comment or reply |
| GET | `/api/comments/captcha/` | Generate CAPTCHA |

### Sorting examples

```text
/api/comments/?ordering=user_name
/api/comments/?ordering=-user_name
/api/comments/?ordering=email
/api/comments/?ordering=-email
/api/comments/?ordering=created_at
/api/comments/?ordering=-created_at
```

Pagination:

```text
/api/comments/?page=2
```

### Comment creation fields

- `user_name` — required; Latin letters and digits.
- `email` — required; valid email address.
- `home_page` — optional URL.
- `text` — required comment text.
- `parent` — optional parent comment ID.
- `captcha_key` — CAPTCHA identifier.
- `captcha_value` — CAPTCHA answer.
- `attachment` — optional file.

File uploads use `multipart/form-data`.

## WebSocket

Clients connect to:

```text
/ws/comments/
```

When a new comment is created, Django Channels broadcasts a `comment_created` event.

The Vue client receives this notification and reloads the comments through the REST API without refreshing the page.

The local Docker setup uses an in-memory channel layer and a single Daphne process. A multi-instance production deployment should use a shared channel layer such as Redis.

## Project Structure

```text
comments-spa/
├── comments/               # Django models, API and WebSocket
├── comments_spa/           # Django settings, URLs and ASGI
├── frontend/               # Vue.js application
├── nginx/                  # Reverse proxy configuration
├── Dockerfile              # Django container
├── Dockerfile.render       # Production Docker image for Render
├── compose.yaml            # Docker services
├── requirements.txt        # Python dependencies
├── comments_spa.mwb        # Database EER diagram (MySQL Workbench)
├── .dockerignore
├── .gitignore
├── .env.example
├── manage.py
└── README.md
```

## Database Schema

The database schema is documented in the `comments_spa.mwb` file, located in the project root.

To view the EER diagram:

1. Install MySQL Workbench 8.0 CE.
2. Open MySQL Workbench.
3. Select **File → Open Model**.
4. Choose `comments_spa.mwb`.

The diagram includes two application tables:

- `comments_comment` — stores comments and nested replies.
- `comments_commentattachment` — stores file attachment references.

The diagram shows the self-referencing relationship for nested comments and the one-to-one relationship between comments and attachments.

**Note:** The application uses PostgreSQL. The MySQL Workbench model is provided for database structure visualization only and is not used to initialize the PostgreSQL database. Django migrations manage the actual database schema.

## Production Deployment

The live application is deployed on Render:

<https://comments-spa-c83f.onrender.com/>

The production environment uses:

- **Render** — hosting and Docker-based application deployment.
- **Neon PostgreSQL** — persistent PostgreSQL database.
- **Cloudinary** — persistent storage for JPG, PNG, GIF, and TXT attachments.
- **Django Channels and Daphne** — WebSocket communication.
- **Nginx** — reverse proxy.

The production configuration uses `Dockerfile.render` and `nginx/render.conf`.

The local Docker environment uses PostgreSQL and local media storage. In production, uploaded attachments are stored in Cloudinary so they remain available after application redeployment.

Sensitive environment variables and service credentials are configured outside the Git repository.

## Security

- Django ORM is used for database queries.
- CAPTCHA is validated and consumed within a database transaction.
- Username, email, text, HTML and attachments are validated server-side.
- Allowed HTML tags and link schemes are restricted.
- Credentials are stored outside the Git repository.
- WebSocket origins are checked by Django Channels.

For an internet-facing production deployment, configure HTTPS, appropriate hosts, CSRF protections, shared channel infrastructure if using multiple workers, and additional security hardening.

## Notes

This project was developed as a test assignment. The Docker configuration provides a reproducible local demonstration environment.

## Author

[Volodymyr Kunaiev](https://github.com/Kunaiev-Vladimir)

[Developer Portfolio](https://my-portfolio-wkh8.onrender.com)
