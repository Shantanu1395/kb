#!/usr/bin/env python3
"""
Gallery-dl Instagram Downloader
Uses gallery-dl library for Instagram downloads
"""

import os
import sys
import ssl
import urllib3
import subprocess
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

def check_gallery_dl():
    """Check if gallery-dl is installed"""
    try:
        result = subprocess.run(['gallery-dl', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ gallery-dl version: {result.stdout.strip()}")
            return True
    except:
        pass
    
    print("❌ gallery-dl not found. Install with: pip install gallery-dl")
    return False

def download_reel(url, output_dir="downloads"):
    """Download Instagram reel using gallery-dl"""
    
    if not check_gallery_dl():
        return None
    
    setup_ssl_bypass()
    
    shortcode = extract_shortcode(url)
    if not shortcode:
        print(f"❌ Could not extract shortcode from: {url}")
        return None
    
    print(f"📥 Downloading reel with gallery-dl: {shortcode}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        # Run gallery-dl command
        cmd = [
            'gallery-dl',
            '--dest', str(output_path),
            '--filename', f'{shortcode}_gallery_dl.{{extension}}',
            url
        ]
        
        print("⬇️  Running gallery-dl...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Find downloaded file
            video_files = list(output_path.glob(f"{shortcode}_gallery_dl.*"))
            
            if video_files:
                video_file = video_files[0]
                file_size = os.path.getsize(video_file) / (1024 * 1024)
                print(f"✅ Downloaded: {video_file} ({file_size:.2f} MB)")
                return video_file
            else:
                print(f"❌ Download file not found")
                return None
        else:
            print(f"❌ gallery-dl failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ gallery-dl timed out")
        return None
    except Exception as e:
        print(f"❌ gallery-dl download failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("🎬 Gallery-dl Instagram Downloader")
        print("=" * 40)
        print("\nUsage:")
        print("python gallery_dl_method.py <instagram_url>")
        print("\nExample:")
        print("python gallery_dl_method.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        print("\nRequirements:")
        print("pip install gallery-dl")
        print("\nNote:")
        print("- Command-line tool for downloading from various sites")
        print("- May have better success with some Instagram posts")
        return
    
    url = sys.argv[1]
    
    print("🚀 Gallery-dl Instagram Downloader")
    print("=" * 50)
    
    result = download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
    else:
        print("\n❌ Download failed")
        print("\n💡 Try aggressive_ssl_bypass.py for better success rate")

if __name__ == "__main__":
    main()