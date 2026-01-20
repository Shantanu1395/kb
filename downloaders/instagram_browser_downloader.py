#!/usr/bin/env python3
"""
Instagram Browser-Style Downloader
Uses browser automation to bypass detection
"""

import os
import sys
import time
import requests
import json
import re
from pathlib import Path
import ssl
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

class InstagramBrowserDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
        # Rotate through different browser signatures
        self.user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.current_ua_index = 0
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with browser-like headers"""
        ua = self.user_agents[self.current_ua_index]
        
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def _rotate_user_agent(self):
        """Rotate to next user agent"""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        self._setup_session()
        print(f"🔄 Rotated to user agent {self.current_ua_index + 1}")
    
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
    
    def _get_page_with_retries(self, url, max_retries=3):
        """Get page with retries and user agent rotation"""
        for attempt in range(max_retries):
            try:
                print(f"🌐 Attempt {attempt + 1}: Fetching {url}")
                
                # Add random delay to seem more human
                time.sleep(2 + attempt)
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    print(f"⏳ Rate limited, waiting {30 * (attempt + 1)} seconds...")
                    time.sleep(30 * (attempt + 1))
                    self._rotate_user_agent()
                else:
                    print(f"❌ HTTP {response.status_code}")
                    if attempt < max_retries - 1:
                        self._rotate_user_agent()
                        
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    self._rotate_user_agent()
                    time.sleep(10 * (attempt + 1))
        
        return None
    
    def _extract_video_url_methods(self, html_content):
        """Try multiple methods to extract video URL"""
        
        # Method 1: Look for video_url in various formats
        patterns = [
            r'"video_url":"([^"]+)"',
            r'"videoUrl":"([^"]+)"',
            r'contentUrl":"([^"]+\.mp4[^"]*)"',
            r'"src":"([^"]+\.mp4[^"]*)"',
            r'video_url&quot;:&quot;([^&]+)&quot;',
            r'"video_versions":\[{"url":"([^"]+)"',
            r'{"url":"([^"]+\.mp4[^"]*)"[^}]*"width"',
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, html_content)
            if matches:
                video_url = matches[0].replace('\\u0026', '&').replace('\\/', '/').replace('&amp;', '&')
                print(f"✅ Found video URL using method {i + 1}")
                return video_url
        
        # Method 2: Look for JSON data
        json_patterns = [
            r'window\._sharedData = ({.*?});',
            r'window\.__additionalDataLoaded\([^,]+,({.*?})\);',
            r'"GraphVideo"[^}]+({[^}]+})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                try:
                    data = json.loads(match)
                    video_url = self._extract_from_json(data)
                    if video_url:
                        print("✅ Found video URL in JSON data")
                        return video_url
                except:
                    continue
        
        return None
    
    def _extract_from_json(self, data):
        """Recursively search for video URL in JSON data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['video_url', 'videoUrl', 'src'] and isinstance(value, str) and '.mp4' in value:
                    return value
                elif isinstance(value, (dict, list)):
                    result = self._extract_from_json(value)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._extract_from_json(item)
                if result:
                    return result
        return None
    
    def download_reel(self, url, output_dir="downloads"):
        """Download Instagram reel with browser-like behavior"""
        
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            print(f"❌ Could not extract shortcode from: {url}")
            return None
        
        print(f"📥 Downloading reel: {shortcode}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Try different URL formats
        url_formats = [
            f"https://www.instagram.com/p/{shortcode}/",
            f"https://www.instagram.com/reel/{shortcode}/",
            f"https://instagram.com/p/{shortcode}/",
        ]
        
        for url_format in url_formats:
            print(f"🔍 Trying URL format: {url_format}")
            
            response = self._get_page_with_retries(url_format)
            if not response:
                continue
            
            html_content = response.text
            
            # Check if we got blocked
            if 'login' in html_content.lower() and 'required' in html_content.lower():
                print("🔐 Login required - trying next method...")
                continue
            
            # Extract video URL
            video_url = self._extract_video_url_methods(html_content)
            
            if video_url:
                return self._download_video_file(video_url, shortcode, output_path)
        
        print(f"❌ All methods failed for {shortcode}")
        return None
    
    def _download_video_file(self, video_url, shortcode, output_path):
        """Download the actual video file"""
        try:
            print(f"⬇️  Downloading video file...")
            
            # Use a fresh session for video download
            video_session = requests.Session()
            video_session.verify = False
            video_session.headers.update({
                'User-Agent': self.session.headers['User-Agent'],
                'Referer': 'https://www.instagram.com/',
            })
            
            response = video_session.get(video_url, stream=True, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ Failed to download video: {response.status_code}")
                return None
            
            # Save video file
            video_file = output_path / f"{shortcode}_browser.mp4"
            
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
        print("🎬 Instagram Browser-Style Downloader")
        print("=" * 40)
        print("\nUsage:")
        print("python instagram_browser_downloader.py <instagram_url>")
        print("\nExample:")
        print("python instagram_browser_downloader.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        return
    
    url = sys.argv[1]
    
    print("🚀 Instagram Browser-Style Downloader")
    print("=" * 50)
    
    downloader = InstagramBrowserDownloader()
    result = downloader.download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
    else:
        print("\n❌ Download failed")

if __name__ == "__main__":
    main()