#!/usr/bin/env python3
"""
API-based Instagram Downloader
Uses third-party APIs to download Instagram content
"""

import os
import sys
import requests
import re
import time
from pathlib import Path
import ssl
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

class APIInstagramDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
        # List of free Instagram downloader APIs
        self.apis = [
            {
                'name': 'RapidAPI Instagram',
                'url': 'https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index',
                'method': 'GET',
                'headers': {
                    'X-RapidAPI-Key': 'demo',  # Would need real key
                    'X-RapidAPI-Host': 'instagram-downloader-download-instagram-videos-stories.p.rapidapi.com'
                },
                'params_key': 'url'
            },
            {
                'name': 'SaveInsta API',
                'url': 'https://v3.saveinsta.app/api/ajaxSearch',
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'data_key': 'q'
            },
            {
                'name': 'SnapInsta API',
                'url': 'https://snapinsta.app/api/convert',
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
                },
                'json_key': 'url'
            }
        ]
    
    def _extract_shortcode(self, url):
        """Extract shortcode from Instagram URL"""
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
    
    def _try_saveinsta_method(self, url):
        """Try SaveInsta-style API"""
        try:
            print("🔄 Trying SaveInsta method...")
            
            api_url = 'https://v3.saveinsta.app/api/ajaxSearch'
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://saveinsta.app/',
                'Origin': 'https://saveinsta.app'
            }
            
            data = {
                'q': url,
                'vt': 'home'
            }
            
            response = self.session.post(api_url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and result['data']:
                    # Look for video URL in response
                    html_content = result['data']
                    
                    # Extract download links
                    video_patterns = [
                        r'href="([^"]+\.mp4[^"]*)"',
                        r'data-href="([^"]+\.mp4[^"]*)"',
                        r'"url":"([^"]+\.mp4[^"]*)"'
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, html_content)
                        if matches:
                            video_url = matches[0]
                            print("✅ Found video URL via SaveInsta API")
                            return video_url
            
            return None
            
        except Exception as e:
            print(f"❌ SaveInsta method failed: {e}")
            return None
    
    def _try_snapinsta_method(self, url):
        """Try SnapInsta-style method"""
        try:
            print("🔄 Trying SnapInsta method...")
            
            # First get the page to extract necessary tokens
            page_url = 'https://snapinsta.app/'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            page_response = self.session.get(page_url, headers=headers, timeout=30)
            
            if page_response.status_code == 200:
                # Try to submit the URL
                api_url = 'https://snapinsta.app/api/convert'
                
                json_data = {
                    'url': url
                }
                
                api_headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': headers['User-Agent'],
                    'Referer': 'https://snapinsta.app/',
                    'Origin': 'https://snapinsta.app'
                }
                
                response = self.session.post(api_url, headers=api_headers, json=json_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Look for video URL in various possible response formats
                    if 'url' in result:
                        print("✅ Found video URL via SnapInsta API")
                        return result['url']
                    elif 'download_url' in result:
                        print("✅ Found video URL via SnapInsta API")
                        return result['download_url']
            
            return None
            
        except Exception as e:
            print(f"❌ SnapInsta method failed: {e}")
            return None
    
    def _try_direct_extraction(self, url):
        """Try direct extraction from Instagram mobile"""
        try:
            print("🔄 Trying direct mobile extraction...")
            
            # Try mobile Instagram with different approaches
            mobile_urls = [
                url.replace('www.instagram.com', 'm.instagram.com'),
                url.replace('instagram.com', 'm.instagram.com'),
                url + '?__a=1',
                url + '?__a=1&__d=dis'
            ]
            
            headers = {
                'User-Agent': 'Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x2340; samsung; SM-G975F; beyond2; exynos9820; en_US; 314665256)',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            for test_url in mobile_urls:
                try:
                    response = self.session.get(test_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Look for video URLs
                        video_patterns = [
                            r'"video_url":"([^"]+)"',
                            r'"videoUrl":"([^"]+)"',
                            r'"video_versions":\[{"url":"([^"]+)"'
                        ]
                        
                        for pattern in video_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                video_url = matches[0].replace('\\u0026', '&').replace('\\/', '/')
                                print("✅ Found video URL via direct extraction")
                                return video_url
                
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Direct extraction failed: {e}")
            return None
    
    def download_reel(self, url, output_dir="downloads"):
        """Download Instagram reel using API methods"""
        
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            print(f"❌ Could not extract shortcode from: {url}")
            return None
        
        print(f"📥 Downloading reel via APIs: {shortcode}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Try different methods
        methods = [
            self._try_saveinsta_method,
            self._try_snapinsta_method,
            self._try_direct_extraction
        ]
        
        for method in methods:
            video_url = method(url)
            if video_url:
                result = self._download_video_file(video_url, shortcode, output_path)
                if result:
                    return result
            
            # Wait between attempts
            time.sleep(2)
        
        print(f"❌ All API methods failed for {shortcode}")
        return None
    
    def _download_video_file(self, video_url, shortcode, output_path):
        """Download the actual video file"""
        try:
            print(f"⬇️  Downloading video file from API...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://www.instagram.com/',
                'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8'
            }
            
            response = self.session.get(video_url, headers=headers, stream=True, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ Failed to download video: {response.status_code}")
                return None
            
            # Save video file
            video_file = output_path / f"{shortcode}_api.mp4"
            
            with open(video_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(video_file) / (1024 * 1024)
            print(f"✅ Downloaded: {video_file} ({file_size:.2f} MB)")
            
            return video_file
            
        except Exception as e:
            print(f"❌ Video download failed: {e}")
            return None

def main():
    if len(sys.argv) < 2:
        print("🎬 API Instagram Downloader")
        print("=" * 40)
        print("\nUsage:")
        print("python api_instagram_downloader.py <instagram_url>")
        print("\nExample:")
        print("python api_instagram_downloader.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        return
    
    url = sys.argv[1]
    
    print("🚀 API Instagram Downloader")
    print("=" * 50)
    
    downloader = APIInstagramDownloader()
    result = downloader.download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
    else:
        print("\n❌ Download failed")

if __name__ == "__main__":
    main()