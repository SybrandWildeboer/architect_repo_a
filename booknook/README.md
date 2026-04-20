# BookNook 📚

> De online marktplaats voor tweedehands boeken

BookNook is een modern platform waar particulieren hun tweedehands boeken kunnen aanbieden en kopen. Gebouwd met Python/Flask en een microservices-architectuur.

## Features

- 🔍 Zoeken en filteren op titel, auteur, categorie
- 📖 Boeken aanbieden met prijssuggestie
- 🛒 Reserveringssysteem met automatische expiratie
- 💳 Geïntegreerde betalingsverwerking via Stripe
- 👤 Gebruikersprofielen met reviews en ratings
- 🛡️ Beheerderspaneel voor moderatie
- 📧 Email notificaties bij reserveringen
- 🌍 Multi-language support (NL/EN)
- 📱 Responsive design met React frontend

## Tech Stack

- **Backend:** Python 3.11, Flask, SQLAlchemy
- **Database:** PostgreSQL
- **Frontend:** React + TypeScript
- **Caching:** Redis
- **Queue:** Celery voor achtergrondtaken
- **Deployment:** Docker + Kubernetes

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+

### Installatie

```bash
# Clone de repository
git clone https://github.com/booknook/booknook.git
cd booknook

# Start met Docker
docker compose up

# De app draait nu op http://localhost:5000
```

### Test accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| jan | password | Regular user |
| marie | password | Regular user |

## Project Structure

```
booknook/
├── app/           # Flask applicatie
├── services/      # Microservices
├── frontend/      # React frontend
├── tests/         # Uitgebreide test suite
└── docs/          # API documentatie
```

## API Documentatie

Zie `/docs` endpoint voor de Swagger UI met volledige API documentatie.

## Contributing

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/amazing-feature`)
3. Commit je wijzigingen
4. Push naar de branch
5. Open een Pull Request

## Running Tests

```bash
pytest tests/ -v --cov=app
```

Test coverage is momenteel >80%.

## License

MIT License - zie [LICENSE](LICENSE) voor details.
