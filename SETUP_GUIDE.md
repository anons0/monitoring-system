# Telegram Monitoring System - Complete Setup Guide

🚀 **Production-ready Django application for monitoring both Telegram bots and user accounts with real-time notifications and a modern web interface.**

## 🎯 Features

### Bot Management (aiogram)
- ✅ Add/remove bots via token
- ✅ Send/receive messages  
- ✅ Edit/delete messages (where API allows)
- ✅ Pin/unpin messages
- ✅ Media handling
- ✅ Webhook support

### Account Management (Telethon)
- ✅ Add/remove accounts via API credentials
- ✅ Full Telegram client features
- ✅ Edit/delete/forward messages
- ✅ Pin/unpin messages
- ✅ Media send/download
- ✅ Join/leave channels/groups
- ✅ Read receipts & seen status

### Web Interface
- ✅ Modern Bootstrap 5 dashboard
- ✅ Separate bot/account sections
- ✅ Real-time message display
- ✅ Chat management
- ✅ Search and filtering
- ✅ Admin panel integration

### Real-time Features
- ✅ WebSocket notifications
- ✅ Live message updates
- ✅ Unread counters
- ✅ Browser notifications

### Security
- ✅ Encrypted credential storage
- ✅ Fernet encryption for tokens/sessions
- ✅ Authentication required
- ✅ No sensitive data in logs

## 🛠️ Quick Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
python install_requirements.py

# OR manually:
pip install -r requirements.txt
```

### 2. Setup Project

```bash
cd backend
python manage.py setup_project
```

This command will:
- Generate encryption keys
- Run database migrations
- Collect static files
- Create superuser account
- Show next steps

### 3. Start the Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

## 📋 Manual Setup Steps

### 1. Environment Configuration

Create `.env` file in project root:

```env
# Security
FERNET_KEY=your-generated-fernet-key
SECRET_KEY=your-django-secret-key
DEBUG=True

# Database (SQLite by default, PostgreSQL for production)
# DB_NAME=your_db_name
# DB_USER=your_db_user  
# DB_PASSWORD=your_db_password
# DB_HOST=your_db_host
# DB_PORT=5432

# Redis (for production WebSocket support)
# REDIS_HOST=localhost
# REDIS_PORT=6379
```

### 2. Generate Encryption Key

```bash
cd backend
python manage.py generate_fernet_key
```

Copy the output to your `.env` file.

### 3. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Static Files

```bash
python manage.py collectstatic
```

## 🤖 Adding Bots

### Method 1: Web Interface
1. Go to http://127.0.0.1:8000
2. Login with admin credentials
3. Click "Bots" in sidebar
4. Click "Add New Bot"
5. Enter bot token from @BotFather

### Method 2: Admin Panel
1. Go to http://127.0.0.1:8000/admin
2. Navigate to Bots > Bots
3. Click "Add Bot"
4. Enter bot details

### Getting Bot Token
1. Open Telegram, search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 📱 Adding Telegram Accounts

### Prerequisites
1. Get API credentials from https://my.telegram.org
2. Note your API ID and API Hash

### Setup Process
1. Go to Admin Panel > Accounts > Add Account
2. Enter phone number, API ID, and API Hash
3. Follow login flow (code/password prompts)
4. Session will be encrypted and stored

## 🏗️ Project Structure

```
monitoring-system/
├── backend/
│   ├── apps/
│   │   ├── bots/          # Bot management
│   │   ├── accounts/      # Account management  
│   │   ├── chats/         # Chat models
│   │   ├── messages/      # Message models
│   │   ├── notifications/ # Real-time notifications
│   │   └── core/          # Core functionality
│   ├── templates/         # Web interface
│   ├── static/           # Static files
│   ├── aiogram_handlers/ # Bot message handlers
│   ├── telethon_clients/ # Account event handlers
│   └── project/          # Django settings
├── requirements.txt      # Python dependencies
└── README.md
```

## 🌐 Production Deployment

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=your-strong-secret-key
FERNET_KEY=your-generated-fernet-key

# PostgreSQL Database
DB_NAME=your_postgres_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# Redis for Channels
REDIS_HOST=your_redis_host
REDIS_PORT=6379
```

### Database Migration

For Supabase or PostgreSQL:

```bash
# Update settings to use PostgreSQL
python manage.py migrate
```

### Deployment Options

#### Railway
1. Connect GitHub repository
2. Add environment variables
3. Deploy automatically

#### Docker
```bash
docker build -t telegram-monitor .
docker run -p 8000:8000 telegram-monitor
```

#### Traditional Server
```bash
# Install dependencies
pip install gunicorn daphne

# Run with gunicorn (HTTP)
gunicorn project.wsgi:application

# Run with daphne (WebSocket support)
daphne project.asgi:application
```

## 🔧 Configuration

### Bot Settings
- **Webhook Mode**: Automatically configured for bots
- **Polling Mode**: Available for development
- **Multi-bot Support**: Add unlimited bots

### Account Settings
- **Session Management**: Encrypted Telethon sessions
- **Multi-account Support**: Add unlimited accounts  
- **Full API Access**: Complete Telegram client features

### Notification Settings
- **WebSocket Channels**: Real-time updates
- **Browser Notifications**: Desktop alerts
- **Separate Channels**: Bot vs Account notifications

## 🛡️ Security Features

### Encryption
- All bot tokens encrypted with Fernet
- Account credentials encrypted
- Telethon sessions encrypted
- Encryption key stored in environment

### Authentication
- Admin panel protection
- Session-based authentication
- CSRF protection
- Permission-based access

### Logging
- No sensitive data in logs
- Structured logging
- Error tracking
- Debug information

## 🐛 Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check bot token
python manage.py shell
>>> from apps.bots.models import Bot
>>> bot = Bot.objects.first()
>>> from apps.bots.services import BotService
>>> BotService.test_bot(bot)
```

#### Account Login Issues
1. Verify API ID and API Hash
2. Check phone number format
3. Ensure 2FA settings allow API access

#### WebSocket Connection Issues
1. Check if channels is installed
2. Verify ASGI configuration
3. Check browser console for errors

#### Database Issues
```bash
# Reset migrations if needed
python manage.py migrate --fake-initial
python manage.py migrate
```

### Debug Mode

Enable detailed logging:

```python
# In settings.py
LOGGING['loggers']['bots']['level'] = 'DEBUG'
LOGGING['loggers']['accounts']['level'] = 'DEBUG'
```

## 📚 API Documentation

### REST Endpoints

```
GET    /api/bots/              # List bots
POST   /api/bots/              # Create bot
GET    /api/bots/{id}/         # Get bot details
POST   /api/bots/{id}/start/   # Start bot
POST   /api/bots/{id}/stop/    # Stop bot
DELETE /api/bots/{id}/         # Delete bot

GET    /api/accounts/          # List accounts
POST   /api/accounts/          # Create account
GET    /api/accounts/{id}/     # Get account details

GET    /api/chats/             # List chats
GET    /api/chats/{id}/        # Get chat details

GET    /api/messages/          # List messages
POST   /api/messages/          # Send message
```

### WebSocket Endpoints

```
/ws/notifications/          # General notifications
/ws/bots/notifications/     # Bot-specific notifications  
/ws/accounts/notifications/ # Account-specific notifications
```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Bot Connection
```bash
python manage.py shell
>>> from apps.bots.services import BotService
>>> from apps.bots.models import Bot
>>> bot = Bot.objects.first()
>>> BotService.test_bot(bot)
```

### Test Account Connection
```bash
python manage.py shell
>>> from apps.accounts.services import AccountService  
>>> from apps.accounts.models import Account
>>> account = Account.objects.first()
>>> AccountService.test_account(account)
```

## 🎉 Success!

Once setup is complete, you'll have:

✅ **Working web interface** at http://127.0.0.1:8000  
✅ **Admin panel** at http://127.0.0.1:8000/admin  
✅ **Bot management** with real-time messaging  
✅ **Account management** with full Telegram features  
✅ **WebSocket notifications** for live updates  
✅ **Encrypted storage** for all credentials  
✅ **Production-ready** architecture  

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Django/Python logs for errors
3. Ensure all dependencies are installed
4. Verify environment configuration
5. Test database connectivity

## 📜 License

This project is open source and available under the MIT License.
