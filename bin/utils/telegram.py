import requests
from core.config import Config
from core.device import DeviceInfo


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_completion_notification(self, device_info: DeviceInfo, config: Config):
        message = self._format_completion_message(device_info, config)
        self._send_message(message)
    
    def _format_completion_message(self, device_info: DeviceInfo, config: Config) -> str:
        message = f"<b>Brand: {device_info.brand}</b>\\n"
        message += f"<b>Device: {device_info.codename}</b>\\n"
        message += f"<b>Platform: {device_info.platform}</b>\\n"
        message += f"<b>Android Version:</b> {device_info.android_version}\\n"
        
        if device_info.kernel_version:
            message += f"<b>Kernel Version:</b> {device_info.kernel_version}\\n"
        
        message += f"<b>Fingerprint:</b> {device_info.fingerprint}\\n"
        
        repo_name = device_info.get_repo_name()
        if config.github_token:
            message += f'<a href="https://github.com/{config.git_org}/{repo_name}/">GitHub Repository</a>'
        elif config.gitlab_token:
            gitlab_host = config.get('gitlab_host', 'https://gitlab.com')
            message += f'<a href="{gitlab_host}/{config.git_org}/{repo_name}/">GitLab Repository</a>'
        
        return message
    
    def _send_message(self, message: str):
        url = f"{self.base_url}/sendMessage"
        data = {
            'text': message,
            'chat_id': self.chat_id,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Telegram notification failed: {response.text}")