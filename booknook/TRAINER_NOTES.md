# TRAINER NOTES - BookNook Architecture Training

> **Dit document is ALLEEN voor de trainer.** Niet delen met deelnemers.

## Overzicht van Ingebouwde Problemen

### 1. Verkeerde Laagscheiding

| Probleem | Locatie |
|----------|---------|
| Database queries direct in route-handlers | `app/routes.py` regels 162-165 (login), 188-192 (register), 68-78 (book_list) |
| HTML rendering gemengd met business logic | `app/routes.py` - de `create_book()` functie doet validatie, DB operaties, EN template rendering |
| Validatielogica verspreid over drie lagen | Prijs validatie in: `app/utils.py:validate_price()`, `app/book_manager.py:create_book()`, `app/static/app.js:form submit handler` |
| Directe DB operaties in admin routes | `app/admin_routes.py` regels 60-64, 75-85 (duplicate van book_manager) |

### 2. God-classes en Spaghetti

| Probleem | Locatie |
|----------|---------|
| BookManager god-class (400+ regels) | `app/book_manager.py` - Doet: CRUD, pricing, notifications, search, recommendations, reserveringen, reviews, statistieken |
| utils.py grab-bag | `app/utils.py` - 30 ongerelateerde helpers van auth decorators tot shipping berekeningen |

### 3. Impliciete Coupling

| Probleem | Locatie |
|----------|---------|
| Globale state via module-level dict | `app/__init__.py` regels 13-16: `SESSION_DATA = {}` en `ACTIVE_RESERVATIONS = {}` |
| Circulaire imports met late imports | `app/__init__.py` regel 40-41, `app/utils.py` regel 141-143 (get_site_stats), `app/book_manager.py` regel 333 |
| Config via os.environ op willekeurige plekken | `app/book_manager.py` regel 228 (MAX_RESERVATIONS), `app/__init__.py` regel 26-28, `app/LEGACY_payment_processor.py` regel 33 |

### 4. Lekkende Abstracties

| Probleem | Locatie |
|----------|---------|
| Repository geeft ORM-objecten terug | `app/repository.py` - alle `find_*` methodes retourneren SQLAlchemy model instances |
| Transacties lekken naar view-laag | `app/repository.py` regels 35-37: `save()` doet geen commit, caller moet dat doen |
| Service layer die alleen doorverwijst | `app/services.py` - bijna elke methode is een one-liner die de repository aanroept |

### 5. Inconsistente Patterns

| Probleem | Locatie |
|----------|---------|
| Drie manieren van error handling | `book_manager.py:create_book()` returns (None, "error"), `book_manager.py:update_book()` raises ValueError, `book_manager.py:get_book()` returns None |
| Twee manieren om config te lezen | `app/__init__.py:get_config_value()` functie (niet gebruikt!), vs directe `os.environ.get()` overal |
| Mix van class-based en function-based views | `app/routes.py`: BookAPIView (class-based) naast alle function-based routes |

---

## Red Herrings

### 1. "TODO: refactor this mess" bij goede code
**Locatie:** `app/book_manager.py` regels 1, 26, en 166-169

De pricing logic (methodes `calculate_suggested_price`, `get_price_statistics`, `apply_bulk_discount`) is eigenlijk **correct en goed gestructureerd**. De multipliers zijn helder, de berekening is transparant. Het probleem is niet de code zelf, maar dat het in een god-class zit.

**Test voor deelnemers:** Wie zegt dat de pricing logic slecht is vs. wie herkent dat het probleem de *locatie* is, niet de *implementatie*?

### 2. LEGACY_payment_processor.py
**Locatie:** `app/LEGACY_payment_processor.py`

Dit bestand ziet eruit als dode code, maar wordt actief gebruikt:
- Import in `app/book_manager.py` regel 333: `from app.LEGACY_payment_processor import process_hold`
- Import in `app/admin_routes.py` regel 31: `from app.LEGACY_payment_processor import get_payment_summary`

**Test voor deelnemers:** Wie stelt voor dit te verwijderen zonder de imports te checken?

---

## Subtiele Problemen

### 1. N+1 Query in Book List
**Locatie:** `app/templates/book_list.html` regel 87: `{{ book.seller.username }}`

In de template wordt voor elk boek `book.seller` lazy-loaded, wat een aparte query per boek triggert. Bij 50 boeken = 51 queries. De `search_books()` methode in `app/book_manager.py` laadt alleen boeken, niet de sellers.

**Hoe te ontdekken:** Laat deelnemers SQL logging aanzetten (`SQLALCHEMY_ECHO=True`) en de boekenlijst bekijken.

### 2. Race Condition in Reservering
**Locatie:** `app/book_manager.py` regels 214-240

Tussen de check `if book.status != 'available'` en de update `book.status = 'reserved'` is er geen locking. Twee gelijktijdige requests kunnen beide succesvol hetzelfde boek reserveren.

**Hoe te ontdekken:** Vraag deelnemers: "Wat gebeurt er als twee gebruikers tegelijk op 'Reserve' klikken?"

### 3. Timezone Bug
**Locatie:** 
- `app/models.py` regels 19, 46-47: `datetime.now()` (lokale tijd)
- `app/models.py` regel 97: `datetime.utcnow()` (ActivityLog gebruikt UTC!)
- `app/utils.py` regel 79: `time_ago()` vergelijkt altijd met `datetime.now()`

ActivityLog entries worden opgeslagen in UTC, maar weergegeven alsof het lokale tijd is. De `time_ago()` helper vergelijkt naïef `datetime.now()` met timestamps die soms UTC zijn.

**Hoe te ontdekken:** Laat deelnemers kijken naar tijdsweergaven in het activity log - in sommige timezones kloppen ze niet.

### 4. SQLite/PostgreSQL Case-Sensitivity Bug
**Locatie:** `app/book_manager.py` regels 135-142

De `LIKE` operator is case-insensitive in SQLite maar case-sensitive in PostgreSQL. De zoekfunctie werkt perfect in development (SQLite) maar mist resultaten in productie (PostgreSQL) voor zoektermen met hoofdletters.

**Hoe te ontdekken:** Laat deelnemers zoeken op "harry potter" vs "Harry Potter" en bespreek wat er in productie zou gebeuren.

---

## Bonus Problemen (niet in de instructie, voor de trainer)

### Bonus 1: In-Memory State Verliest Data bij Restart
**Locatie:** `app/__init__.py` regels 13-16, `app/book_manager.py`

`SESSION_DATA`, `ACTIVE_RESERVATIONS`, en de `_notification_queue` in BookManager zijn allemaal in-memory. Bij een server restart (of bij meerdere workers) gaat deze data verloren. De `LEGACY_payment_processor.py` heeft hetzelfde probleem met `_payment_holds` en `_processed_payments`.

### Bonus 2: Onveilige Password Hashing
**Locatie:** `app/utils.py` regels 45-47

`hash_password()` gebruikt SHA256 zonder salt. Dit is niet geschikt voor productie (rainbow table attacks). Maar dit is bewust GEEN focus van deze repo (security is repo B's domein). Wel interessant als een deelnemer het opmerkt.

### Bonus 3: Side Effect in Getter
**Locatie:** `app/book_manager.py` regels 84-88

`get_book()` verhoogt de `views_count` en doet een `db.session.commit()`. Dit is een onverwachte side effect in wat een getter zou moeten zijn. Het betekent ook dat elke API call naar `/api/books/<id>` de view count verhoogt, inclusief bots, crawlers, en de admin die boeken bekijkt.

---

## Misleidende README

De README (`booknook/README.md`) bevat de volgende onjuistheden:

| Claim in README | Werkelijkheid |
|----------------|---------------|
| "microservices-architectuur" | Het is een monoliet |
| "React + TypeScript frontend" | Het is Jinja2 templates + vanilla JS |
| "Redis caching" | In-memory Python dicts |
| "Celery voor achtergrondtaken" | Geen queue, alles synchroon |
| "Kubernetes deployment" | Alleen Docker Compose |
| "Email notificaties" | Alleen in-memory queue, geen echte emails |
| "Multi-language support" | Niet geïmplementeerd |
| "Stripe betalingsverwerking" | Eigen simpele simulator |
| "Swagger UI documentatie" | Bestaat niet |
| "Test coverage >80%" | Er zijn 3 simpele tests |
| "services/ directory" | Bestaat niet |
| "frontend/ directory" | Bestaat niet |
| "docs/ directory" | Bestaat niet |

**Didactisch doel:** Deelnemers leren dat README's niet blind vertrouwd mogen worden. Een goede architect verifieert claims door de code te inspecteren.

---

## Suggesties voor de Training

### Fase 1: Handmatige Verkenning (zonder AI)
1. Laat deelnemers de README lezen en een eerste architectuurdiagram tekenen
2. Laat ze de code verkennen en hun diagram bijwerken
3. Bespreek de discrepanties - wat leert dit over documentatie?

### Fase 2: Problemen Identificeren
1. Laat elk team 3-5 architectuurproblemen documenteren
2. Laat ze per probleem een verbetervoorstel schrijven
3. Bespreek de red herring - wie trapte erin?

### Fase 3: Met AI als Versterker
1. Laat deelnemers dezelfde analyse herhalen met AI-tools
2. Vergelijk de resultaten: vindt AI meer? Minder? Andere dingen?
3. Bespreek wanneer AI meerwaarde heeft vs. wanneer het misleidt

### Fase 4: Verbeterplan
1. Laat teams een architectuur-verbeterplan schrijven
2. Prioriteer de gevonden problemen (impact vs. effort)
3. Schrijf concrete tickets voor de top-5 verbeteringen
