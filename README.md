# Telegram Monitoring System

A comprehensive Django application for monitoring multiple Telegram bots and user accounts with real-time notifications, unified admin dashboard, and encrypted credential storage.

## Features

### Bot Management (aiogram)
- Add/remove bots via token
- Webhook-based message handling
- Send/receive messages
- Basic message management (edit/delete where API allows)
- Real-time status monitoring

### Account Management (Telethon)
- Add/remove accounts via API ID, API Hash, and phone number
- Full Telegram client functionality
- Complete message management (send/edit/delete/forward)
- Media handling
- Channel/group management
- Read receipts and seen status

### Unified Dashboard
- Separate sections for bots and accounts
- Real-time message updates via WebSockets
- Unread message counters
- Search and filtering capabilities
- Responsive web interface

### Security
- All sensitive data encrypted with Fernet
- Secure credential storage
- Django authentication required
- No sensitive data in logs

### Deployment
- Docker support for development
- Railway deployment configuration
- Supabase PostgreSQL integration
- Redis for WebSocket channels

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**For Windows:**
```cmd
start_development.bat
```

**For Linux/macOS:**
```bash
./start_development.sh
```

**Using Python script:**
```bash
python start_server.py
```

### Option 2: Manual Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd monitoring-system
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

5. Generate Fernet key:
```bash
cd backend
python manage.py generate_fernet_key
```

6. Set up database:
```bash
python manage.py migrate
python manage.py createsuperuser
```

7. Run development server with WebSocket support:
```bash
daphne -p 8000 project.asgi:application
```

**Important:** Always run from the `backend` directory or use the provided startup scripts!

### Docker Development

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Access the application at `http://localhost:8000`

### Production Deployment (Railway)

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard:
   - `SECRET_KEY`
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
   - `REDIS_HOST`, `REDIS_PORT`
   - `FERNET_KEY`
3. Deploy automatically via Git push

## Configuration

### Environment Variables

Required environment variables:

```bash
SECRET_KEY=your-django-secret-key
DEBUG=False  # Set to False in production

# Supabase Database
DB_NAME=your-database-name
DB_USER=your-database-user  
DB_PASSWORD=your-database-password
DB_HOST=your-supabase-host
DB_PORT=5432

# Redis (for Django Channels)
REDIS_HOST=your-redis-host
REDIS_PORT=6379

# Encryption key (generate with Fernet.generate_key())
FERNET_KEY=your-base64-fernet-key
```

### Database Schema

The system uses the following main tables:
- `bots` - Bot credentials and status
- `accounts` - Account credentials and status  
- `users` - Telegram users (both bot and account users)
- `chats` - Chat information (separated by type)
- `messages` - All messages with metadata
- `notifications` - System notifications

## Usage

### Adding Bots

1. Go to Admin Dashboard → Bots section
2. Click "Add Bot"
3. Enter bot token (get from @BotFather)
4. Bot will be validated and added
5. Start the bot to begin receiving messages

### Adding Accounts

1. Go to Admin Dashboard → Accounts section
2. Click "Add Account" 
3. Enter API ID, API Hash (from my.telegram.org), and phone number
4. Complete login flow with verification code
5. Handle 2FA if enabled
6. Account will start receiving messages automatically

### Message Management

**Bot Messages:**
- View incoming/outgoing messages
- Send new messages
- Basic editing (limited by Bot API)

**Account Messages:**
- Full message management
- Edit/delete any message
- Forward messages
- Media upload/download
- Pin/unpin messages
- Mark as read

### WebSocket Notifications

Connect to WebSocket endpoints for real-time updates:
- `/ws/bots/notifications/` - Bot-specific notifications
- `/ws/accounts/notifications/` - Account-specific notifications  
- `/ws/notifications/` - All notifications

## API Endpoints

### Bots
- `GET /api/bots/` - List all bots
- `POST /api/bots/add/` - Add new bot
- `POST /api/bots/{id}/start/` - Start bot
- `POST /api/bots/{id}/stop/` - Stop bot

### Accounts  
- `GET /api/accounts/` - List all accounts
- `POST /api/accounts/add/` - Add new account
- `POST /api/accounts/{id}/login/` - Initiate login
- `POST /api/accounts/{id}/verify/` - Verify login code

### Messages
- `GET /api/messages/` - List messages (with filtering)
- `POST /api/messages/send/` - Send message
- `POST /api/messages/{id}/edit/` - Edit message
- `POST /api/messages/{id}/delete/` - Delete message

### Chats
- `GET /api/chats/` - List all chats
- `GET /api/chats/bot-chats/` - List bot chats
- `GET /api/chats/account-chats/` - List account chats

## Architecture

```
┌──────────────┐
│   Web UI     │
│(Django/HTML) │  
└─────┬────────┘
      │ WebSocket + REST
┌─────┴──────────────────────┐
│     Django Backend         │
│                            │
│  ┌─────────────┐  ┌───────┐│
│  │Bot Service  │  │Account││
│  │(aiogram)    │  │Service││
│  │             │  │(Teletho││
│  └─────────────┘  └───────┘│
└────────────────────────────┘
```

### Key Components

- **Django Backend**: Main application server
- **Bot Service**: aiogram-based bot management
- **Account Service**: Telethon-based account management  
- **WebSocket Layer**: Real-time notifications via Django Channels
- **Database**: PostgreSQL via Supabase
- **Cache/Queue**: Redis for channels and background tasks

## Testing

Run the test suite:

```bash
cd backend
python manage.py test
```

For load testing with multiple bots/accounts:
```bash
# TODO: Implement load testing scripts
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'project'**
   - **Problem**: Running daphne from wrong directory
   - **Solution**: Use `cd backend && daphne -p 8000 project.asgi:application` or use the provided startup scripts

2. **Port 8000 already in use**
   - **Problem**: Another process is using port 8000
   - **Solution**: Kill the process (`netstat -ano | findstr :8000`) or use different port (`daphne -p 8001 project.asgi:application`)

3. **Bot not receiving messages**: Check webhook configuration and bot token

4. **Account login fails**: Verify API ID/Hash and phone number format

5. **WebSocket connection fails**: Check Redis connection and authentication

6. **Database connection issues**: Verify Supabase credentials and SSL settings

7. **Django runserver vs Daphne**
   - **Problem**: Django's runserver doesn't support WebSockets
   - **Solution**: Always use Daphne for development: `daphne project.asgi:application`

### Logs

Check Django logs for detailed error information:
```bash
tail -f logs/django.log  # If logging to file
docker-compose logs -f web  # Docker setup
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Create GitHub issue
- Check documentation
- Review logs for error details