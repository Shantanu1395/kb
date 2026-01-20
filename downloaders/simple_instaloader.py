#!/usr/bin/env python3
"""
Simple Instaloader Method
Basic Instagram downloader using instaloader library
"""

import os
import sys
import ssl
import urllib3
import instaloader
from pathlib import Path

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
    """Download Instagram reel using simple instaloader"""
    
    setup_ssl_bypass()
    
    shortcode = extract_shortcode(url)
    if not shortcode:
        print(f"❌ Could not extract shortcode from: {url}")
        return None
    
    print(f"📥 Downloading reel: {shortcode}")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # Create Instaloader instance
        L = instaloader.Instaloader(
            dirname_pattern=output_dir,
            filename_pattern='{date_utc}_UTC',
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )
        
        # Get post from shortcode
        print("🔍 Fetching post information...")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        print(f"📹 Found post by: @{post.owner_username}")
        
        if not post.is_video:
            print(f"❌ Post {shortcode} is not a video")
            return None
        
        print("⬇️  Downloading video...")
        L.download_post(post, target=shortcode)
        
        # Find downloaded video file
        output_path = Path(output_dir)
        video_files = list(output_path.glob("**/*.mp4"))
        
        if video_files:
            video_file = video_files[0]
            print(f"✅ Downloaded: {video_file}")
            return video_file
        else:
            print(f"❌ Video file not found")
            return None
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("🎬 Simple Instaloader Method")
        print("=" * 40)
        print("\nUsage:")
        print("python simple_instaloader.py <instagram_url>")
        print("\nExample:")
        print("python simple_instaloader.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        return
    
    url = sys.argv[1]
    
    print("🚀 Simple Instaloader Method")
    print("=" * 50)
    
    result = download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
    else:
        print("\n❌ Download failed")

if __name__ == "__main__":
    main()