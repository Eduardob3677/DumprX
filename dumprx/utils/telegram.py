import requests
from typing import Optional, Dict, Any
from dumprx.core.config import Config
from dumprx.utils.console import console, info, success, warning, error

class TelegramNotifier:
    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.get('telegram.enabled', False)
        self.token = config.get('telegram.token') or self._get_legacy_token()
        self.chat_id = config.get('telegram.chat_id') or self._get_legacy_chat_id()
        
    def send_notification(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send notification to Telegram"""
        if not self.enabled:
            return True
            
        if not self.token or not self.chat_id:
            warning("Telegram token or chat_id not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            success("Telegram notification sent")
            return True
            
        except Exception as e:
            error(f"Failed to send Telegram notification: {e}")
            return False
    
    def send_extraction_start(self, firmware_info: Dict[str, Any]) -> bool:
        """Send extraction start notification"""
        message = f"""
🔄 *DumprX Extraction Started*

📱 *Device*: {firmware_info.get('device_name', 'Unknown')}
📦 *File*: {firmware_info.get('filename', 'Unknown')}
📐 *Size*: {firmware_info.get('file_size', 'Unknown')}
⏰ *Time*: {firmware_info.get('start_time', 'Unknown')}
        """.strip()
        
        return self.send_notification(message)
    
    def send_extraction_complete(self, result_info: Dict[str, Any]) -> bool:
        """Send extraction completion notification"""
        status = "✅ *Completed*" if result_info.get('success') else "❌ *Failed*"
        
        message = f"""
{status} *DumprX Extraction*

📱 *Device*: {result_info.get('device_name', 'Unknown')}
⏱️ *Duration*: {result_info.get('duration', 'Unknown')}
📊 *Partitions*: {result_info.get('partitions_count', 0)}
📁 *Files*: {result_info.get('files_count', 0)}
        """
        
        if result_info.get('git_url'):
            message += f"\n🔗 *Repository*: {result_info['git_url']}"
        
        if result_info.get('error'):
            message += f"\n⚠️ *Error*: {result_info['error']}"
        
        return self.send_notification(message.strip())
    
    def send_download_progress(self, download_info: Dict[str, Any]) -> bool:
        """Send download progress notification"""
        message = f"""
📥 *Download Progress*

📦 *File*: {download_info.get('filename', 'Unknown')}
📊 *Progress*: {download_info.get('progress', 0)}%
💾 *Downloaded*: {download_info.get('downloaded_size', 'Unknown')}
📐 *Total*: {download_info.get('total_size', 'Unknown')}
        """.strip()
        
        return self.send_notification(message)
    
    def send_error(self, error_message: str, context: Optional[str] = None) -> bool:
        """Send error notification"""
        message = f"❌ *DumprX Error*\n\n{error_message}"
        
        if context:
            message += f"\n\n*Context*: {context}"
        
        return self.send_notification(message)
    
    def _get_legacy_token(self) -> Optional[str]:
        """Get Telegram token from legacy file"""
        try:
            with open('.tg_token', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
    
    def _get_legacy_chat_id(self) -> Optional[str]:
        """Get Telegram chat ID from legacy file"""
        try:
            with open('.tg_chat', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.token:
            error("Telegram token not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            bot_info = response.json()
            if bot_info.get('ok'):
                success(f"Telegram bot connected: @{bot_info['result']['username']}")
                return True
            else:
                error("Invalid Telegram bot token")
                return False
                
        except Exception as e:
            error(f"Failed to test Telegram connection: {e}")
            return False