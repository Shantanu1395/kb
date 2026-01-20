#!/usr/bin/env python3
"""
yt-dlp Instagram Downloader
Uses yt-dlp library for Instagram downloads
"""

import os
import sys
import ssl
import urllib3
from pathlib import Path

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("❌ yt-dlp not installed. Install with: pip install yt-dlp")

def setup_ssl_bypass():
    """Apply SSL bypass for corporate networks"""
    print("🔧 Applying SSL bypass...")
    
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings()
    
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    print("✅ SSL bypass applied")

def extract_shortcode(url):
    """Extract shortcode from Instagram URL"""
    import re
    patterns = [
        r'/p/([^/?]+)',
        r'/reel/([^/?]+)',
        r'/tv/([^/?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_reel(url, output_dir="downloads"):
    """Download Instagram reel using yt-dlp"""
    
    if not YTDLP_AVAILABLE:
        print("❌ yt-dlp not available")
        return None
    
    setup_ssl_bypass()
    
    shortcode = extract_shortcode(url)
    if not shortcode:
        print(f"❌ Could not extract shortcode from: {url}")
        return None
    
    print(f"📥 Downloading reel with yt-dlp: {shortcode}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': str(output_path / f'{shortcode}_ytdlp.%(ext)s'),
            'format': 'best[ext=mp4]',
            'no_warnings': False,
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("🔍 Extracting video info...")
            
            # Extract info
            info = ydl.extract_info(url, download=False)
            
            if not info:
                print(f"❌ Could not extract info for {shortcode}")
                return None
            
            print(f"📹 Found video: {info.get('title', 'Unknown')}")
            
            # Download
            print("⬇️  Downloading video...")
            ydl.download([url])
            
            # Find downloaded file
            video_files = list(output_path.glob(f"{shortcode}_ytdlp.*"))
            
            if video_files:
                video_file = video_files[0]
                file_size = os.path.getsize(video_file) / (1024 * 1024)
                print(f"✅ Downloaded: {video_file} ({file_size:.2f} MB)")
                return video_file
            else:
                print(f"❌ Download file not found")
                return None
                
    except Exception as e:
        print(f"❌ yt-dlp download failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("🎬 yt-dlp Instagram Downloader")
        print("=" * 40)
        print("\nUsage:")
        print("python ytdlp_method.py <instagram_url>")
        print("\nExample:")
        print("python ytdlp_method.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        print("\nRequirements:")
        print("pip install yt-dlp")
        return
    
    url = sys.argv[1]
    
    print("🚀 yt-dlp Instagram Downloader")
    print("=" * 50)
    
    result = download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
    else:
        print("\n❌ Download failed")

if __name__ == "__main__":
    main()