# Sweep Rules and Commands

## Common Commands

### Development
```bash
# Start development server
cd backend && python manage.py runserver

# Run migrations
cd backend && python manage.py migrate

# Create superuser
cd backend && python manage.py createsuperuser

# Generate Fernet key
cd backend && python manage.py generate_fernet_key

# Start bots
cd backend && python manage.py start_bots

# Start accounts
cd backend && python manage.py start_accounts

# Run tests
cd backend && python manage.py test
```

### Docker
```bash
# Build and run development environment
docker-compose up --build

# Run migrations in container
docker-compose exec web python manage.py migrate

# Create superuser in container
docker-compose exec web python manage.py createsuperuser
```

### Production (Railway)
- Deployment is automatic via git push
- Environment variables must be set in Railway dashboard
- Database migrations run automatically during deploy

## Code Style Preferences

### Python/Django
- Use Django best practices and conventions
- Type hints for function parameters and returns
- Docstrings for classes and complex methods
- Async/await for I/O operations when possible
- Comprehensive error handling and logging

### Database
- Use proper indexes for frequently queried fields
- Separate models by domain (bots, accounts, messages, etc.)
- Encrypted storage for sensitive data
- Proper foreign key relationships

### Security
- All sensitive data must be encrypted with Fernet
- No secrets in code or logs
- Authentication required for all admin endpoints
- Proper CSRF protection

## Project Structure

```
backend/
├── project/           # Django settings and config
├── apps/             # Django applications
│   ├── core/         # Shared models and utilities
│   ├── bots/         # Bot management (aiogram)
│   ├── accounts/     # Account management (Telethon)
│   ├── chats/        # Chat models and views
│   ├── messages/     # Message models and handling
│   └── notifications/# WebSocket notifications
├── aiogram_handlers/ # aiogram message handlers
├── telethon_clients/ # Telethon event handlers
└── templates/        # HTML templates
```

## Architecture Notes

### Bot vs Account Separation
- Bots and Accounts are completely separate in the UI
- Different WebSocket channels: `/ws/bots/notifications/` and `/ws/accounts/notifications/`
- Separate chat types: `bot_chat` vs `account_chat`
- Never mix bot and account messages in the same view

### Real-time Updates
- Django Channels for WebSocket communication
- Redis as message broker
- Separate notification channels for bots and accounts
- Auto-updating unread counters

### Encryption
- Fernet symmetric encryption for all sensitive data
- Bot tokens, API credentials, and sessions are encrypted
- Encryption key stored in environment variable
- Never log decrypted sensitive data

## Deployment

### Railway Configuration
- Uses Dockerfile for containerization  
- Automatic migrations during deployment
- Environment variables configured in Railway dashboard
- Static files served by Django in production

### Required Environment Variables
- `SECRET_KEY`: Django secret key
- `FERNET_KEY`: Encryption key (generate with management command)
- `DB_*`: Supabase database credentials
- `REDIS_*`: Redis connection details

## Testing Strategy

- Unit tests for models and encryption
- Integration tests for API endpoints
- Mock external APIs (Telegram Bot API, MTProto)
- Load testing for multiple concurrent bots/accounts
- WebSocket connection testing