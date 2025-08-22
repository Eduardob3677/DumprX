import re
import json
import math
import requests
import humanize
from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

console = Console()

class AFHDownloader:
    def __init__(self):
        self.mirror_url = r"https://androidfilehost.com/libs/otf/mirrors.otf.php"
        self.url_matchers = [
            re.compile(r"fid=(?P<id>\d+)")
        ]
    
    class Mirror:
        def __init__(self, **entries):
            self.__dict__.update(entries)
    
    def download_file(self, url, fname, fsize):
        with Progress(
            "[progress.description]{task.description}",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Downloading {fname}", total=fsize)
            
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(fname, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
    
    def get_file_info(self, url):
        data = requests.head(url)
        rsize = int(data.headers['Content-Length'])
        size = humanize.naturalsize(rsize, binary=True)
        
        content_disposition = data.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        else:
            filename = url.split('/')[-1] or 'download'
        
        return (rsize, size, filename)
    
    def download_servers(self, fid):
        cook = requests.get(f"https://androidfilehost.com/?fid={fid}")
        post_data = {
            "submit": "submit",
            "action": "getdownloadmirrors",
            "fid": fid
        }
        mirror_headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/63.0.3239.132 Safari/537.36"),
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"https://androidfilehost.com/?fid={fid}",
            "X-MOD-SBB-CTYPE": "xhr",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        mirror_data = requests.post(
            self.mirror_url,
            headers=mirror_headers,
            data=post_data,
            cookies=cook.cookies
        )
        
        try:
            mirror_json = json.loads(mirror_data.text)
            if not mirror_json["STATUS"] == "1" or not mirror_json["CODE"] == "200":
                return None
            
            mirror_opts = []
            for mirror in mirror_json["MIRRORS"]:
                mirror_opts.append(self.Mirror(**mirror))
            return mirror_opts
        except Exception:
            return None
    
    def match_url(self, url):
        for pattern in self.url_matchers:
            res = pattern.search(url)
            if res is not None:
                return res
        return None
    
    def download(self, url):
        file_match = self.match_url(url)
        if not file_match:
            raise Exception("This does not appear to be a supported AFH link.")
        
        file_id = file_match.group('id')
        console.print("Obtaining available download servers...")
        
        servers = self.download_servers(file_id)
        if servers is None:
            raise Exception("Unable to retrieve download servers, rate limited.")
        
        server = servers[0]
        console.print(f"Downloading from {server.name}...")
        
        rsize, size, fname = self.get_file_info(server.url)
        console.print(f"Size: {size} | Filename: {fname}")
        
        self.download_file(server.url, fname, rsize)
        return [fname]