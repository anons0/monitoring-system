# Generated migration for auto-reply functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0002_bot_commands_bot_description_bot_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bot',
            name='auto_reply_enabled',
            field=models.BooleanField(default=True, help_text='Whether to send auto-reply to user messages'),
        ),
        migrations.AddField(
            model_name='bot',
            name='auto_reply_message',
            field=models.TextField(blank=True, default='📦 Ботдан фойдаланиш тартиби\nУшбу бот фақат рўйхатдан ўтган фойдаланувчилар учун юк маълумотларини олишга мўлжалланган.\nАгар сиз рўйхатдан ўтмаган бўлсангиз, @jahon_yuklari_admin_4 га мурожаат қилинг.\n\nЮкни олиш ёки етказиш манзилида ҳар қандай ўзгариш бўлса, @jahon_yuklari_admin_4 га тўғридан-тўғри мурожаат қилинг.\n\n🚫 Бу ботга ёзманг!', help_text='Auto-reply message to send to users (except for /start command)'),
        ),
    ]