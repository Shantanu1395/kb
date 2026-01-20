#!/usr/bin/env python3
"""
Instagrapi Instagram Downloader
Uses instagrapi library for Instagram downloads
"""

import os
import sys
import ssl
import urllib3
import shutil
from pathlib import Path

try:
    from instagrapi import Client as InstagrapiClient
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False
    print("❌ instagrapi not installed. Install with: pip install instagrapi")

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
    """Download Instagram reel using instagrapi"""
    
    if not INSTAGRAPI_AVAILABLE:
        print("❌ instagrapi not available")
        return None
    
    setup_ssl_bypass()
    
    shortcode = extract_shortcode(url)
    if not shortcode:
        print(f"❌ Could not extract shortcode from: {url}")
        return None
    
    print(f"📥 Downloading reel with instagrapi: {shortcode}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        # Initialize Instagrapi client
        client = InstagrapiClient()
        
        print("🔍 Fetching post information...")
        
        # Get media info
        media_pk = client.media_pk_from_code(shortcode)
        media_info = client.media_info(media_pk)
        
        if media_info.media_type != 2:  # 2 = video
            print(f"❌ Post {shortcode} is not a video")
            return None
        
        print(f"📹 Found video by: @{media_info.user.username}")
        
        # Download video
        print("⬇️  Downloading video...")
        video_path = client.video_download(media_pk, folder=str(output_path))
        
        if video_path and os.path.exists(video_path):
            # Rename to include shortcode
            clean_video_path = output_path / f"{shortcode}_instagrapi.mp4"
            shutil.move(str(video_path), str(clean_video_path))
            
            file_size = os.path.getsize(clean_video_path) / (1024 * 1024)
            print(f"✅ Downloaded: {clean_video_path} ({file_size:.2f} MB)")
            
            return clean_video_path
        else:
            print(f"❌ Video download failed")
            return None
            
    except Exception as e:
        print(f"❌ instagrapi download failed: {e}")
        
        if "login_required" in str(e).lower():
            print("💡 This method requires Instagram login for some posts")
            print("💡 Try the aggressive_ssl_bypass.py method instead")
        
        return None

def main():
    if len(sys.argv) < 2:
        print("🎬 Instagrapi Instagram Downloader")
        print("=" * 40)
        print("\nUsage:")
        print("python instagrapi_method.py <instagram_url>")
        print("\nExample:")
        print("python instagrapi_method.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        print("\nRequirements:")
        print("pip install instagrapi")
        print("\nNote:")
        print("- May require Instagram login for some posts")
        print("- Works better for public posts")
        return
    
    url = sys.argv[1]
    
    print("🚀 Instagrapi Instagram Downloader")
    print("=" * 50)
    
    result = download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
    else:
        print("\n❌ Download failed")
        print("\n💡 Try aggressive_ssl_bypass.py for better success rate")

if __name__ == "__main__":
    main()