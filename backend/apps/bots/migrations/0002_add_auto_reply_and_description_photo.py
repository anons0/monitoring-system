# Generated migration for auto-reply and description photo fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0001_initial'),
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
        migrations.AddField(
            model_name='bot',
            name='description_photo',
            field=models.ImageField(blank=True, help_text='Bot description photo', null=True, upload_to='bot_descriptions/'),
        ),
    ]