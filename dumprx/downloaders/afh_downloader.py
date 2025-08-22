import re
import cgi
import json
import math
import requests
from pathlib import Path

mirror_url = r"https://androidfilehost.com/libs/otf/mirrors.otf.php"
url_matchers = [
    re.compile(r"fid=(?P<id>\d+)")
]

class Mirror:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def download_file(url, fname, fsize, console=None):
    dat = requests.get(url, stream=True)
    with open(fname, 'wb') as f:
        total_chunks = math.floor(fsize / 4096) + 1
        downloaded_chunks = 0
        
        for chunk in dat.iter_content(chunk_size=4096):
            f.write(chunk)
            f.flush()
            downloaded_chunks += 1
            
            if console and downloaded_chunks % 100 == 0:
                progress = (downloaded_chunks / total_chunks) * 100
                console.print(f"[blue]📥 Progress: {progress:.1f}%[/blue]")

def get_file_info(url):
    data = requests.head(url)
    rsize = int(data.headers['Content-Length'])
    ftype, fdata = cgi.parse_header(data.headers['Content-Disposition'])
    return (rsize, fdata['filename'])

def download_servers(fid):
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
    mirror_data = requests.post(mirror_url,
                                headers=mirror_headers,
                                data=post_data,
                                cookies=cook.cookies)
    try:
        mirror_json = json.loads(mirror_data.text)
        if not mirror_json["STATUS"] == "1" or not mirror_json["CODE"] == "200":
            return None
        else:
            mirror_opts = []
            for mirror in mirror_json["MIRRORS"]:
                mirror_opts.append(Mirror(**mirror))
            return mirror_opts
    except Exception as e:
        return None

def match_url(url):
    for pattern in url_matchers:
        res = pattern.search(url)
        if res is not None:
            return res
    return None

def download_afh(url, output_dir, console=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_match = match_url(url)
    if file_match:
        file_id = file_match.group('id')
        if console:
            console.print("[blue]📥 Obtaining available download servers...[/blue]")
        
        servers = download_servers(file_id)
        if servers == None:
            if console:
                console.print("[red]❌ Unable to retrieve download servers[/red]")
            return None
        
        server = servers[0]
        if console:
            console.print(f"[blue]📥 Downloading from {server.name}...[/blue]")
        
        rsize, fname = get_file_info(server.url)
        
        output_file = output_dir / fname
        download_file(server.url, output_file, rsize, console)
        
        if console:
            console.print("[green]✅ Download complete![/green]")
        
        return output_file
    else:
        if console:
            console.print("[red]❌ This does not appear to be a supported AFH link[/red]")
        return None