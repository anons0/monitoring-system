import logging
import asyncio
from typing import Optional
from django.utils import timezone
from aiogram import Bot as AiogramBot
from aiogram.types import BotCommand, BotCommandScope, MenuButton, MenuButtonWebApp, WebAppInfo
from aiogram.exceptions import TelegramAPIError
from apps.core.encryption import encryption_service

logger = logging.getLogger('bots')

class BotProfileService:
    """Service for managing bot profiles on Telegram"""
    
    @staticmethod
    def update_bot_profile(bot) -> bool:
        """Update bot profile on Telegram"""
        try:
            return asyncio.run(BotProfileService._update_bot_profile_async(bot))
        except Exception as e:
            logger.error(f"Error updating bot profile for {bot.username}: {e}")
            return False
    
    @staticmethod
    async def _update_bot_profile_async(bot) -> bool:
        """Async method to update bot profile"""
        try:
            # Get decrypted token
            token = encryption_service.decrypt(bot.token_enc)
            aiogram_bot = AiogramBot(token=token)
            
            # Update bot name if provided
            if bot.first_name:
                await aiogram_bot.set_my_name(name=bot.first_name)
                logger.info(f"Updated name for bot {bot.username}: {bot.first_name}")
            
            # Update bot description if provided
            if bot.description:
                await aiogram_bot.set_my_description(description=bot.description)
                logger.info(f"Updated description for bot {bot.username}")
            
            # Update bot short description if provided
            if bot.short_description:
                await aiogram_bot.set_my_short_description(short_description=bot.short_description)
                logger.info(f"Updated short description for bot {bot.username}")
            
            # Note: Telegram Bot API doesn't allow bots to change their own profile photos
            # Profile photos must be changed manually through @BotFather or Telegram client
            if bot.profile_photo:
                logger.info(f"Profile photo uploaded for bot {bot.username} - stored locally. To update on Telegram, change via @BotFather")
                # The photo is stored locally and will be displayed in the web interface
            
            # Update bot commands if provided
            if bot.commands:
                try:
                    commands = []
                    for cmd in bot.commands:
                        if isinstance(cmd, dict) and 'command' in cmd and 'description' in cmd:
                            commands.append(BotCommand(
                                command=cmd['command'],
                                description=cmd['description']
                            ))
                    
                    if commands:
                        await aiogram_bot.set_my_commands(commands)
                        logger.info(f"Updated commands for bot {bot.username}: {len(commands)} commands")
                except Exception as e:
                    logger.warning(f"Failed to update commands for {bot.username}: {e}")
            
            # Update menu button if provided
            if bot.menu_button_text and bot.menu_button_url:
                try:
                    menu_button = MenuButtonWebApp(
                        text=bot.menu_button_text,
                        web_app=WebAppInfo(url=bot.menu_button_url)
                    )
                    await aiogram_bot.set_chat_menu_button(menu_button=menu_button)
                    logger.info(f"Updated menu button for bot {bot.username}")
                except Exception as e:
                    logger.warning(f"Failed to update menu button for {bot.username}: {e}")
            
            # Close bot session
            await aiogram_bot.session.close()
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Telegram API error updating bot {bot.username}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating bot {bot.username}: {e}")
            return False
    
    @staticmethod
    def sync_bot_info(bot) -> bool:
        """Sync bot information from Telegram"""
        try:
            return asyncio.run(BotProfileService._sync_bot_info_async(bot))
        except Exception as e:
            logger.error(f"Error syncing bot info for {bot.username}: {e}")
            return False
    
    @staticmethod
    async def _sync_bot_info_async(bot) -> bool:
        """Async method to sync bot information from Telegram"""
        try:
            # Get decrypted token
            token = encryption_service.decrypt(bot.token_enc)
            aiogram_bot = AiogramBot(token=token)
            
            # Get bot info
            bot_info = await aiogram_bot.get_me()
            
            # Update local bot info
            updated = False
            if bot.username != bot_info.username:
                bot.username = bot_info.username
                updated = True
            
            if bot.first_name != bot_info.first_name:
                bot.first_name = bot_info.first_name or ''
                updated = True
            
            # Get bot description
            try:
                desc = await aiogram_bot.get_my_description()
                if desc and bot.description != desc.description:
                    bot.description = desc.description or ''
                    updated = True
            except Exception:
                pass
            
            # Get bot short description
            try:
                short_desc = await aiogram_bot.get_my_short_description()
                if short_desc and bot.short_description != short_desc.short_description:
                    bot.short_description = short_desc.short_description or ''
                    updated = True
            except Exception:
                pass
            
            # Get bot commands
            try:
                commands = await aiogram_bot.get_my_commands()
                commands_data = [
                    {'command': cmd.command, 'description': cmd.description}
                    for cmd in commands
                ]
                if bot.commands != commands_data:
                    bot.commands = commands_data
                    updated = True
            except Exception:
                pass
            
            # Get profile photos
            try:
                photos = await aiogram_bot.get_user_profile_photos(user_id=bot.bot_id, limit=1)
                if photos.total_count > 0:
                    photo = photos.photos[0][-1]  # Get largest photo
                    photo_url = f"https://api.telegram.org/file/bot{token}/{(await aiogram_bot.get_file(photo.file_id)).file_path}"
                    if bot.profile_photo_url != photo_url:
                        bot.profile_photo_url = photo_url
                        updated = True
            except Exception:
                pass
            
            if updated:
                bot.save()
                logger.info(f"Synced bot info for {bot.username}")
            
            # Close bot session
            await aiogram_bot.session.close()
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Telegram API error syncing bot {bot.username}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error syncing bot {bot.username}: {e}")
            return False
    
    @staticmethod
    def get_bot_profile_info(bot) -> dict:
        """Get current bot profile information from Telegram"""
        try:
            return asyncio.run(BotProfileService._get_bot_profile_info_async(bot))
        except Exception as e:
            logger.error(f"Error getting bot profile info for {bot.username}: {e}")
            return {}
    
    @staticmethod
    async def _get_bot_profile_info_async(bot) -> dict:
        """Async method to get bot profile information"""
        try:
            # Get decrypted token
            token = encryption_service.decrypt(bot.token_enc)
            aiogram_bot = AiogramBot(token=token)
            
            info = {}
            
            # Get basic bot info
            bot_info = await aiogram_bot.get_me()
            info['bot_info'] = {
                'id': bot_info.id,
                'username': bot_info.username,
                'first_name': bot_info.first_name,
                'is_bot': bot_info.is_bot,
                'can_join_groups': bot_info.can_join_groups,
                'can_read_all_group_messages': bot_info.can_read_all_group_messages,
                'supports_inline_queries': bot_info.supports_inline_queries
            }
            
            # Get descriptions
            try:
                desc = await aiogram_bot.get_my_description()
                info['description'] = desc.description if desc else ''
            except Exception:
                info['description'] = ''
            
            try:
                short_desc = await aiogram_bot.get_my_short_description()
                info['short_description'] = short_desc.short_description if short_desc else ''
            except Exception:
                info['short_description'] = ''
            
            # Get commands
            try:
                commands = await aiogram_bot.get_my_commands()
                info['commands'] = [
                    {'command': cmd.command, 'description': cmd.description}
                    for cmd in commands
                ]
            except Exception:
                info['commands'] = []
            
            # Close bot session
            await aiogram_bot.session.close()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting bot profile info: {e}")
            return {}
    
    @staticmethod
    def update_bot_menu_button(bot) -> bool:
        """Update bot menu button on Telegram"""
        try:
            return asyncio.run(BotProfileService._update_bot_menu_button_async(bot))
        except Exception as e:
            logger.error(f"Error updating menu button for {bot.username}: {e}")
            return False
    
    @staticmethod
    async def _update_bot_menu_button_async(bot) -> bool:
        """Async method to update bot menu button"""
        try:
            # Get decrypted token
            token = encryption_service.decrypt(bot.token_enc)
            aiogram_bot = AiogramBot(token=token)
            
            # Update menu button if provided
            if bot.menu_button_text and bot.menu_button_url:
                try:
                    menu_button = MenuButtonWebApp(
                        text=bot.menu_button_text,
                        web_app=WebAppInfo(url=bot.menu_button_url)
                    )
                    await aiogram_bot.set_chat_menu_button(menu_button=menu_button)
                    logger.info(f"Updated menu button for bot {bot.username}")
                except Exception as e:
                    logger.warning(f"Failed to update menu button for {bot.username}: {e}")
                    return False
            
            # Close bot session
            await aiogram_bot.session.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating menu button for {bot.username}: {e}")
            return False
    
    @staticmethod
    def update_bot_commands(bot) -> bool:
        """Update bot commands on Telegram"""
        try:
            return asyncio.run(BotProfileService._update_bot_commands_async(bot))
        except Exception as e:
            logger.error(f"Error updating commands for {bot.username}: {e}")
            return False
    
    @staticmethod
    async def _update_bot_commands_async(bot) -> bool:
        """Async method to update bot commands"""
        try:
            # Get decrypted token
            token = encryption_service.decrypt(bot.token_enc)
            aiogram_bot = AiogramBot(token=token)
            
            # Update bot commands if provided
            if bot.commands:
                try:
                    commands = []
                    for cmd in bot.commands:
                        if isinstance(cmd, dict) and 'command' in cmd and 'description' in cmd:
                            commands.append(BotCommand(
                                command=cmd['command'],
                                description=cmd['description']
                            ))
                    
                    if commands:
                        await aiogram_bot.set_my_commands(commands)
                        logger.info(f"Updated commands for bot {bot.username}: {len(commands)} commands")
                except Exception as e:
                    logger.warning(f"Failed to update commands for {bot.username}: {e}")
                    return False
            
            # Close bot session
            await aiogram_bot.session.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating commands for {bot.username}: {e}")
            return False