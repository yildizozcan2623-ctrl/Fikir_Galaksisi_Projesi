import re
from urllib.parse import urlparse, parse_qs

def is_valid_url(url):
    pattern = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
    )
    return bool(pattern.match(url))

def is_valid_github_url(url):
    pattern = re.compile(
        r'^(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/?$'
    )
    return bool(pattern.match(url))

def is_safe_url(url):
    if "<script" in url.lower():
        return False
    return True

def extract_video_id(url):
    """YouTube URL'sinden video ID'sini çıkar"""
    if "youtu.be" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/watch" in url:
        query_params = parse_qs(urlparse(url).query)
        return query_params.get("v", [None])[0]
    return None

def extract_github_repo_info(url):
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            return None, None
            
        owner = path_parts[0]
        repo = path_parts[1]
        
        return owner, repo
    except:
        return None, None
