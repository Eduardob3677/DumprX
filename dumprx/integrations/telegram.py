import asyncio
import aiohttp
from typing import Optional, Dict, Any
from ..core.logger import Logger
from ..core.config import Config

class TelegramBot:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.token = config.telegram_token
        self.chat_id = config.telegram_chat_id or config.telegram.default_chat
        
    async def send_notification(self, firmware_info: Dict[str, Any], git_url: str) -> bool:
        if not self.token:
            self.logger.info("Telegram token not configured, skipping notification")
            return False
            
        message = self._format_message(firmware_info, git_url)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.token}/sendmessage"
                data = {
                    "text": message,
                    "chat_id": self.chat_id,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        self.logger.success("Telegram notification sent")
                        return True
                    else:
                        self.logger.error("Telegram notification failed", f"HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error("Telegram notification error", str(e))
            return False
    
    def _format_message(self, firmware_info: Dict[str, Any], git_url: str) -> str:
        brand = firmware_info.get('brand', 'Unknown')
        codename = firmware_info.get('codename', 'Unknown')
        platform = firmware_info.get('platform', 'Unknown')
        release = firmware_info.get('release', 'Unknown')
        kernel_version = firmware_info.get('kernel_version', '')
        fingerprint = firmware_info.get('fingerprint', 'Unknown')
        branch = firmware_info.get('branch', 'main')
        
        message = f"<b>Brand:</b> {brand}\n"
        message += f"<b>Device:</b> {codename}\n"
        message += f"<b>Platform:</b> {platform}\n"
        message += f"<b>Android Version:</b> {release}\n"
        
        if kernel_version:
            message += f"<b>Kernel Version:</b> {kernel_version}\n"
            
        message += f"<b>Fingerprint:</b> {fingerprint}\n"
        message += f"<a href=\"{git_url}/tree/{branch}/\">Repository Tree</a>"
        
        return message