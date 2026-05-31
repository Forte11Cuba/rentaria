<p align="center">
  <img src="logo/rentaria_logo.png" alt="Rentaria" width="180"/>
</p>

<h1 align="center">Rentaria</h1>

<p align="center">
  Multi-tenant SaaS platform for rental businesses — Bitcoin payments via BTCPay Server, automatic PDF contracts, per-shop configurable booking forms and contracts.
</p>

---

## Stack

- **Backend**: Django 5.x + PostgreSQL
- **Frontend**: Django Templates + Tailwind CSS (CDN) + HTMX + Alpine.js
- **Payments**: BTCPay Server (configured per shop)
- **Emails**: Resend API + `.ics` attachments
- **PDF**: WeasyPrint (rental contracts)
- **Deploy**: Docker Compose + Nginx + Let's Encrypt

---

## Roles

- **Superadmin**: manages the platform (users, shops, global orders)
- **Shop owner**: manages their shops, inventory, booking forms, contracts and orders
- **Customer**: books without an account (public per-shop flow)

---

## Prerequisites

- Docker + Docker Compose v2
- A VPS (Ubuntu/Debian) with a domain pointing to it
- A [Resend](https://resend.com) account with a verified domain
- (Optional, per shop) BTCPay Server with an API key holding `cancreateinvoice` + `canviewinvoices` permissions

---

## Initial setup

### 1. Clone and configure environment

```bash
git clone <repo> rentaria
cd rentaria
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=<long-random-string>
DEBUG=False
ALLOWED_HOSTS=app.yourdomain.com

DB_NAME=rentaria
DB_USER=rentaria
DB_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432

RESEND_API_KEY=re_xxxx

SUPERADMIN_EMAIL=admin@yourdomain.com
SUPERADMIN_PASSWORD=<strong-password>

BASE_DOMAIN=yourdomain.com
APP_URL=https://app.yourdomain.com
```

`BASE_DOMAIN` is used in email sender addresses (`no-reply@{BASE_DOMAIN}`) and `APP_URL` for absolute links.

---

## First deploy (HTTP, before SSL)

Before issuing the SSL certificate, Nginx needs to serve HTTP for the Let's Encrypt challenge:

```bash
cat > nginx.http.conf << 'EOF'
upstream django { server web:8000; }
server {
    listen 80;
    server_name app.yourdomain.com;
    client_max_body_size 20M;
    location /static/ { alias /app/staticfiles/; }
    location /media/  { alias /app/media/; }
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

cp nginx.conf nginx.ssl.conf
cp nginx.http.conf nginx.conf
docker compose up -d
```

### Issue SSL certificate

```bash
docker compose --profile certbot run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d app.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos --no-eff-email
```

### Switch to HTTPS

```bash
cp nginx.ssl.conf nginx.conf
docker compose restart nginx
```

---

## Regular deploy

```bash
docker compose up -d --build
```

`entrypoint.sh` runs automatically on container start:

1. `python manage.py migrate`
2. `python manage.py collectstatic --noinput`
3. `python manage.py init_superadmin`
4. `gunicorn config.wsgi:application --bind 0.0.0.0:8000`

---

## Scheduled tasks (host crontab)

```cron
# Daily SSL renewal
0 3 * * * cd /path/to/rentaria && docker compose --profile certbot run --rm certbot renew && docker compose restart nginx

# Cancel pending Bitcoin orders older than 35 min every 10 min
*/10 * * * * cd /path/to/rentaria && docker compose exec web python manage.py cancelar_ordenes_expiradas
```

---

## Useful commands

```bash
# Tail logs
docker compose logs -f web

# Run migrations manually
docker compose exec web python manage.py migrate

# Create superadmin manually
docker compose exec web python manage.py init_superadmin

# Django shell
docker compose exec web python manage.py shell

# Backup the database
docker compose exec db pg_dump -U rentaria rentaria > backup_$(date +%Y%m%d).sql
```

---

## First-use flow

1. Visit `https://app.yourdomain.com/auth/register/` and create an owner account → it stays in `pending` status
2. The superadmin approves it from `https://app.yourdomain.com/superadmin/users/`
3. The owner receives a welcome email and logs in
4. Creates a shop at `/dashboard/shops/create/`
5. Adds models and units at `/dashboard/shop/<slug>/inventory/`
6. Configures the booking form and the contract template
7. Customers book from `https://app.yourdomain.com/<shop-slug>/`

---

## Main URLs

| Audience | URL |
|---|---|
| Customer (public flow) | `/<shop-slug>/` |
| Bitcoin payment | `/payment/<order_id>/` |
| BTCPay webhook (per shop) | `/payment/webhook/btcpay/` |
| Order confirmation | `/confirmation/<order_id>/` |
| Auth | `/auth/login/`, `/auth/register/`, `/auth/password-reset/` |
| Owner panel | `/dashboard/` |
| Superadmin panel | `/superadmin/` |
| Django admin | `/django-admin/` |

---

## Security

- CSRF enabled on every POST form
- Session and CSRF cookies marked `Secure` in production
- HSTS enabled (1 year, includes subdomains)
- Nginx security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- `SECRET_KEY` always from environment variable
- BTCPay credentials stored per shop in the DB (never in global env vars)
- Media files served directly by Nginx, bypassing Django

---

## Project structure

```
adminsite/
├── config/             # Settings, URLs, WSGI, context processors
├── apps/
│   ├── usuarios/       # Usuario (AbstractUser), auth, registration, roles
│   ├── tiendas/        # Shop model
│   ├── motos/          # ModeloMoto, Moto (unit with plate), PlanPrecio, FotoModelo, CargoMoto
│   ├── reservas/       # Order, LineaOrden, RespuestaCliente, public booking flow
│   ├── formularios/    # CampoFormulario, PlantillaContrato
│   ├── cuentas/        # Per-shop internal accounting (Cuenta, Operacion)
│   └── admin_panel/    # Owner + superadmin views (urls + views + forms)
├── services/
│   ├── btcpay.py       # BTCPay integration
│   ├── confirmacion.py # Order confirmation orchestrator
│   ├── contrato.py     # PDF generation (Markdown → HTML → WeasyPrint)
│   ├── email.py        # Emails via Resend
│   └── whatsapp.py     # Pre-filled WhatsApp link for cash flow
├── templates/
│   ├── base_cliente.html     # Customer flow (dark Rentaria theme)
│   ├── base_admin.html       # Admin shell (light/dark with CSS vars)
│   ├── auth/                 # login, register, pending, password-reset
│   ├── reservas/             # Multi-step customer flow
│   ├── admin_panel/          # Owner panel
│   └── superadmin/           # Global panel
├── static/             # CSS, JS, images (logo, favicon)
├── logo/               # Original logo asset
├── media/              # Runtime uploads (gitignored)
├── nginx.conf          # Nginx HTTPS + SSL
├── nginx.dev.conf      # Nginx for local dev
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
└── manage.py
```

---

## Internationalization

Internal URL paths are in English (`/shop/`, `/inventory/`, `/units/`, `/orders/`, etc.) to ease adding more languages later. Template-visible content is currently in Spanish (primary audience in El Salvador / Latin America).

The term `units` is intentionally generic — it works for motorcycles today and for houses, rooms, bikes or any other rentable asset tomorrow without needing to migrate URLs.

---

## License

MIT.
