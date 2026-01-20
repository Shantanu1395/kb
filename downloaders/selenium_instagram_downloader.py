#!/usr/bin/env python3
"""
Selenium Instagram Downloader
Uses real browser automation to bypass detection
"""

import os
import sys
import time
import requests
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import ssl
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

class SeleniumInstagramDownloader:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome driver with stealth options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Stealth options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        
        # Mobile user agent to get mobile version
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to hide automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome driver initialized")
            
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            print("💡 Make sure Chrome browser is installed")
            sys.exit(1)
    
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
    
    def _human_like_behavior(self):
        """Add human-like delays and behavior"""
        # Random scroll
        self.driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * 500));")
        time.sleep(1 + (time.time() % 2))  # Random delay 1-3 seconds
    
    def download_reel(self, url, output_dir="downloads"):
        """Download Instagram reel using Selenium"""
        
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            print(f"❌ Could not extract shortcode from: {url}")
            return None
        
        print(f"📥 Downloading reel with Selenium: {shortcode}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        try:
            # Navigate to Instagram post
            print("🌐 Loading Instagram page...")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Human-like behavior
            self._human_like_behavior()
            
            # Get page source
            page_source = self.driver.page_source
            
            # Check if we're blocked
            if 'login' in page_source.lower() and 'required' in page_source.lower():
                print("🔐 Login required on main site, trying mobile version...")
                
                # Try mobile Instagram
                mobile_url = url.replace('www.instagram.com', 'm.instagram.com')
                self.driver.get(mobile_url)
                time.sleep(5)
                page_source = self.driver.page_source
            
            # Extract video URL from page source
            video_url = self._extract_video_url(page_source)
            
            if video_url:
                return self._download_video_file(video_url, shortcode, output_path)
            else:
                print("❌ Could not find video URL in page")
                return None
                
        except Exception as e:
            print(f"❌ Selenium download failed: {e}")
            return None
    
    def _extract_video_url(self, html_content):
        """Extract video URL from HTML content"""
        
        # Multiple patterns to find video URL
        patterns = [
            r'"video_url":"([^"]+)"',
            r'"videoUrl":"([^"]+)"',
            r'contentUrl":"([^"]+\.mp4[^"]*)"',
            r'"src":"([^"]+\.mp4[^"]*)"',
            r'video_url&quot;:&quot;([^&]+)&quot;',
            r'"video_versions":\[{"url":"([^"]+)"',
            r'{"url":"([^"]+\.mp4[^"]*)"[^}]*"width"',
            r'<video[^>]+src="([^"]+\.mp4[^"]*)"',
            r'<source[^>]+src="([^"]+\.mp4[^"]*)"'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, html_content)
            if matches:
                video_url = matches[0].replace('\\u0026', '&').replace('\\/', '/').replace('&amp;', '&')
                print(f"✅ Found video URL using pattern {i + 1}")
                return video_url
        
        return None
    
    def _download_video_file(self, video_url, shortcode, output_path):
        """Download the actual video file"""
        try:
            print(f"⬇️  Downloading video file...")
            
            # Use requests with browser headers
            session = requests.Session()
            session.verify = False
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Referer': 'https://www.instagram.com/',
                'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8'
            })
            
            response = session.get(video_url, stream=True, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ Failed to download video: {response.status_code}")
                return None
            
            # Save video file
            video_file = output_path / f"{shortcode}_selenium.mp4"
            
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
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")

def main():
    if len(sys.argv) < 2:
        print("🎬 Selenium Instagram Downloader")
        print("=" * 40)
        print("\nUsage:")
        print("python selenium_instagram_downloader.py <instagram_url> [--show-browser]")
        print("\nExample:")
        print("python selenium_instagram_downloader.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        print("python selenium_instagram_downloader.py 'https://www.instagram.com/reel/DTBkPhSk63f/' --show-browser")
        return
    
    url = sys.argv[1]
    headless = "--show-browser" not in sys.argv
    
    print("🚀 Selenium Instagram Downloader")
    print("=" * 50)
    
    downloader = SeleniumInstagramDownloader(headless=headless)
    
    try:
        result = downloader.download_reel(url)
        
        if result:
            print(f"\n🎉 Success! Downloaded: {result}")
        else:
            print("\n❌ Download failed")
    
    finally:
        downloader.close()

if __name__ == "__main__":
    main()