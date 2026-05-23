# Rittenadministratie — CLAUDE.md

## Project

Flask-webapplicatie voor het bijhouden van zakelijke rittenregistratie. Ingezet op Render.com (gratis tier, 512 MB RAM). Database op Neon.tech (PostgreSQL).

Eigenaar: Pim Lavaleije (pim@lavaleije.nl)

---

## Technische stack

| Onderdeel      | Keuze                                      |
|----------------|--------------------------------------------|
| Backend        | Flask 3.0 + SQLAlchemy                     |
| Database       | Neon.tech PostgreSQL (prod) / SQLite (dev) |
| DB driver      | pg8000 (pure Python, geen libpq nodig)     |
| Frontend       | Bootstrap 5 + Bootstrap Icons              |
| Deployment     | Render.com (free tier)                     |
| Excel export   | openpyxl                                   |
| Odoo koppeling | XML-RPC via `xmlrpc.client`                |
| Authenticatie  | Flask-Login (single user via env vars)     |

---

## Bestanden

```
app.py              — Flask routes en app-logica
models.py           — SQLAlchemy models (Vehicle, Driver, Trip)
odoo_connector.py   — Odoo XML-RPC client (partners/projecten ophalen)
requirements.txt    — Python dependencies
render.yaml         — Render deployment configuratie
templates/          — Jinja2 HTML templates
  base.html
  login.html
  dashboard.html
  ritten_lijst.html
  rit_formulier.html
  kwartaal.html
  instellingen.html
  import.html
```

---

## Database

### Verbinding (productie)

- Host: `ep-aged-credit-al0e0zsu.c-3.eu-central-1.aws.neon.tech`
- Database: `neondb`
- Driver: pg8000 met SSL (`ssl.create_default_context()`)
- `DATABASE_URL` moet beginnen met `postgresql://` — app vervangt dit intern naar `postgresql+pg8000://` en strips `?sslmode=require`

### Models

**Vehicle** — kenteken, merk, model, actief  
**Driver** — naam, email, odoo_user_id  
**Trip** — datum, driver_id, vehicle_id, startlocatie, eindlocatie, beginstand_km, eindstand_km, type (zakelijk/prive), odoo_partner_id/naam, odoo_project_id/naam, omschrijving, notitie

### Kilometerstand logica

- `beginstand_km` van een nieuwe rit = `MAX(eindstand_km)` voor dat voertuig
- `eindstand_km` = beginstand + ingevoerde kilometers
- `Trip.kilometers` is een `@property`: `eindstand_km - beginstand_km`

---

## Authenticatie

Eenvoudige single-user login via Flask-Login. Geen database — credentials komen uit env vars.

```python
class User(UserMixin):
    id = "1"
```

- Inloggen mislukt als `LOGIN_PASSWORD` niet is ingesteld (veilige standaard)
- `remember=True` bij login zodat de sessie blijft na sluiten browser
- Alle routes zijn beveiligd met `@login_required`
- Open routes: `/login`, `/logout`

| Env var          | Omschrijving              |
|------------------|---------------------------|
| `LOGIN_USERNAME` | Inlognaam (standaard: `admin`) |
| `LOGIN_PASSWORD` | Wachtwoord (verplicht instellen) |

---

## Vaste instellingen (business rules)

- **Bestuurder**: standaard "Pim Lavaleije" (Driver.id = 5), maar aanpasbaar per rit via dropdown
- **Voertuig**: standaard "S-581-TK", maar aanpasbaar per rit via dropdown
- **Startlocatie**: standaard inhoud van `HOME_ADDRESS` env var (fallback: "Thuis")
- **Type**: altijd "zakelijk"
- **Heen en terug**: checkbox (standaard aangevinkt) maakt automatisch een tweede rit aan (Van klant → Thuis, zelfde km)
- **Multi-datum**: bij een nieuwe rit kunnen meerdere datums worden opgegeven; de app maakt voor elke datum afzonderlijke ritten aan met doorlopende kilometerstand

---

## Render.com deployment

### Start commando

```
gunicorn app:app --workers 1 --timeout 120
```

`--workers 1` is verplicht vanwege 512 MB RAM limiet. Meerdere workers veroorzaken OOM (SIGKILL).

### Environment variables (handmatig instellen in Render Dashboard)

| Variabele        | Waarde                                        |
|------------------|-----------------------------------------------|
| `SECRET_KEY`     | auto-generated door Render                    |
| `DATABASE_URL`   | Neon connection string (sync: false)          |
| `LOGIN_USERNAME` | gewenste inlognaam (bijv. `pim`)              |
| `LOGIN_PASSWORD` | sterk wachtwoord (verplicht)                  |
| `HOME_ADDRESS`   | volledig thuisadres (bijv. `Dorpsstraat 1, 1234 AB Plaatsnaam`) |
| `ODOO_URL`       | `https://lavaleije-it-solutions.odoo.com`     |
| `ODOO_DB`        | `lavaleije-it-solutions`                      |
| `ODOO_USERNAME`  | `pim@lavaleije.nl`                            |
| `ODOO_PASSWORD`  | (handmatig, sync: false)                      |

**Let op**: `render.yaml` bevat de gewenste waarden maar Render past deze **niet automatisch toe** op een bestaande service. Wijzigingen moeten handmatig worden ingevoerd in het Render Dashboard → Environment.

---

## Odoo koppeling

- `odoo_connector.py` leest env vars **per call** (niet bij `__init__`), zodat Render env vars na deploy worden opgepikt zonder herstart
- Diagnose endpoint: `GET /api/odoo/status` — toont welke vars leeg zijn
- Partners API: `GET /api/odoo/partners?q=<zoekterm>` → geeft `[{id, name, street, zip, city}]`
- Alleen bedrijven (`is_company = True`, `active = True`) worden opgehaald
- Adres wordt in de frontend samengesteld uit street + zip + city (fallback: naam)

### Laatste km auto-fill

`GET /api/laatste-km?partner_id=<id>&partner_naam=<naam>`

Zoekt de meest recente rit naar die klant en geeft de km terug. Zoekt eerst op `odoo_partner_id`, daarna fallback op `odoo_partner_naam` (nodig voor historisch geïmporteerde ritten zonder partner_id).

---

## Functies overzicht

### Rittenlijst (`/ritten`)
- Zoeken op locatie, omschrijving, klant
- Filteren op jaar, maand, type
- Paginering (20 per pagina)
- **Bulk verwijderen**: checkboxes per rij + select-all + actie-balk

### Rit formulier (`/rit/nieuw`, `/rit/<id>/bewerk`)
- Bestuurder en voertuig via dropdown (met default pre-geselecteerd)
- Startlocatie pre-filled vanuit `HOME_ADDRESS` env var
- Klant/eindlocatie met Odoo autocomplete (vult ook adres en laatste km in)
- Multi-datum invoer bij nieuwe rit (meerdere dagen tegelijk)
- Heen-en-terug checkbox

### Kwartaalrapport (`/kwartaal`)
- Overzicht zakelijke en privé km per kwartaal
- Voorbeeld journaalboeking voor kilometervergoeding (km × tarief)
- BTW-correctiepercentage privégebruik auto
- Instelbaar tarief (standaard €0,23/km)
- Kopieerknop en afdrukfunctie

---

## Lokaal draaien

```bash
# Kopieer .env.example naar .env en vul aan
cp .env.example .env

# Installeer dependencies
pip install -r requirements.txt

# Start de app
python app.py
```

SQLite wordt automatisch gebruikt als `DATABASE_URL` niet is ingesteld.

---

## Historische data importeren (groot bestand)

Gebruik **niet** de web-import voor grote bestanden — dit veroorzaakt OOM op Render. Genereer in plaats daarvan SQL lokaal en voer dit uit in de Neon SQL Editor:

1. Lees het Excel-bestand met PowerShell COM-interop (zodat openpyxl niet nodig is)
2. Genereer een `.sql` bestand met `DO $$ ... $$` blokken
3. Plak en voer uit in [console.neon.tech](https://console.neon.tech)

---

## Bekende valkuilen

- **`extract("month", ...) == 0`** levert nooit resultaten op (maanden zijn 1–12). Filter alleen toepassen als `maand != 0`.
- **Duplicate drivers**: na import kunnen er duplicaten ontstaan. Gebruik `UPDATE trip SET driver_id = 5 WHERE driver_id IN (6,7)` gevolgd door `DELETE FROM driver WHERE id IN (6,7)`.
- **pg8000 SSL**: gebruik altijd `ssl.create_default_context()`, niet `ssl_context=True`.
- **openpyxl grote bestanden**: gebruik altijd `read_only=True` om geheugen te sparen.
- **Odoo partner_id vs naam**: geïmporteerde ritten hebben `odoo_partner_naam` maar geen `odoo_partner_id`. Altijd beide kolommen doorzoeken bij lookups.
- **Multi-datum kilometerstand**: bij batch-invoer over meerdere datums loopt de kilometerstand cumulatief door over alle ritten in die batch (inclusief retourritten). Volgorde is gesorteerd op datum.
