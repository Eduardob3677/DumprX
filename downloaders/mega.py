import re
import json
import base64
import subprocess
import requests
from rich.console import Console

console = Console()

class MegaDownloader:
    def __init__(self):
        self.api_url = "https://g.api.mega.co.nz/cs"
    
    def url_str(self, s):
        return s.replace("-", "+").replace("_", "/").replace(",", "")
    
    def json_req(self, data, params=""):
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}{params}", json=data, headers=headers)
        return response.json()
    
    def key_solver(self, key):
        try:
            decoded = base64.b64decode(key + "===")
            return decoded.hex()
        except Exception:
            return ""
    
    def mega_link_vars(self, url):
        if "/folder/" in url or "#F!" in url:
            if "#F!" in url:
                parts = url.split("#F!")[1].split("!")
                fld = "F"
                id_part = parts[0]
                key = parts[1] if len(parts) > 1 else ""
            else:
                parts = url.split("/folder/")[1].split("#")
                fld = "folder"
                id_part = parts[0]
                key = parts[1] if len(parts) > 1 else ""
        else:
            if "#!" in url:
                parts = url.split("#!")[1].split("!")
                fld = ""
                id_part = parts[0]
                key = parts[1] if len(parts) > 1 else ""
            else:
                raise Exception("Invalid Mega URL format")
        
        return fld, id_part, key
    
    def download(self, url):
        console.print("Mega.NZ Website Link Detected")
        
        try:
            fld, id_part, key = self.mega_link_vars(url)
            
            if fld in ["F", "folder"]:
                console.print("Folder download not fully implemented yet")
                console.print("Please use megadl command instead:")
                console.print(f"megadl '{url}'")
                
                try:
                    result = subprocess.run(['megadl', url], check=True, capture_output=True, text=True)
                    return ["folder_downloaded"]
                except subprocess.CalledProcessError as e:
                    raise Exception(f"megadl failed: {e}")
                except FileNotFoundError:
                    raise Exception("megadl not found. Please install megatools package.")
            else:
                console.print("Single file download not fully implemented yet")
                console.print("Please use megadl command instead:")
                console.print(f"megadl '{url}'")
                
                try:
                    result = subprocess.run(['megadl', url], check=True, capture_output=True, text=True)
                    return ["file_downloaded"]
                except subprocess.CalledProcessError as e:
                    raise Exception(f"megadl failed: {e}")
                except FileNotFoundError:
                    raise Exception("megadl not found. Please install megatools package.")
                    
        except Exception as e:
            console.print(f"[red]Error processing Mega URL: {e}[/red]")
            console.print("Falling back to megadl...")
            
            try:
                result = subprocess.run(['megadl', url], check=True, capture_output=True, text=True)
                return ["downloaded_file"]
            except subprocess.CalledProcessError as e:
                raise Exception(f"megadl failed: {e}")
            except FileNotFoundError:
                raise Exception("megadl not found. Please install megatools package.")