#!/usr/bin/env python3
"""
Smart Rate Limit Instagram Downloader
Handles Instagram rate limiting intelligently with exponential backoff
"""

import os
import sys
import time
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import instaloader
import ssl
import urllib3
import certifi

# Apply aggressive SSL bypass
def setup_ssl_bypass():
    """Apply aggressive SSL bypass for corporate networks"""
    print("🔧 Applying SSL bypass for corporate networks...")
    
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    urllib3.disable_warnings()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)
    
    ssl._create_default_https_context = ssl._create_unverified_context
    
    from urllib3.util.ssl_ import create_urllib3_context
    
    def create_insecure_context():
        context = ssl.SSLContext()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    urllib3.util.ssl_.create_urllib3_context = create_insecure_context
    
    print("✅ SSL bypass applied")

class SmartRateLimitDownloader:
    def __init__(self, output_dir="downloads"):
        setup_ssl_bypass()
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Exponential backoff settings
        self.base_delay = 60  # Start with 1 minute
        self.max_delay = 3600  # Max 1 hour
        self.backoff_multiplier = 2
        
        # Rate limiting state
        self.rate_limit_file = Path("rate_limit_state.json")
        self.load_rate_limit_state()
        
        print("✅ Smart rate limit downloader initialized")
    
    def load_rate_limit_state(self):
        """Load rate limiting state from file"""
        if self.rate_limit_file.exists():
            try:
                with open(self.rate_limit_file, 'r') as f:
                    data = json.load(f)
                    self.last_request_time = datetime.fromisoformat(data.get('last_request_time', '2000-01-01'))
                    self.consecutive_failures = data.get('consecutive_failures', 0)
                    self.current_delay = data.get('current_delay', self.base_delay)
            except:
                self.reset_rate_limit_state()
        else:
            self.reset_rate_limit_state()
    
    def reset_rate_limit_state(self):
        """Reset rate limiting state"""
        self.last_request_time = datetime.min
        self.consecutive_failures = 0
        self.current_delay = self.base_delay
    
    def save_rate_limit_state(self):
        """Save rate limiting state to file"""
        data = {
            'last_request_time': self.last_request_time.isoformat(),
            'consecutive_failures': self.consecutive_failures,
            'current_delay': self.current_delay
        }
        with open(self.rate_limit_file, 'w') as f:
            json.dump(data, f)
    
    def should_wait(self):
        """Check if we should wait before making a request"""
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        
        if self.consecutive_failures > 0:
            required_wait = self.current_delay
            if time_since_last < required_wait:
                wait_time = required_wait - time_since_last
                return True, wait_time
        
        return False, 0
    
    def wait_if_needed(self):
        """Wait if rate limiting is active"""
        should_wait, wait_time = self.should_wait()
        
        if should_wait:
            print(f"⏳ Rate limit active. Waiting {wait_time:.0f} seconds...")
            print(f"📊 Consecutive failures: {self.consecutive_failures}")
            print(f"🕐 Current delay: {self.current_delay}s")
            
            # Show countdown
            for remaining in range(int(wait_time), 0, -1):
                print(f"\r⏱️  Waiting: {remaining}s remaining...", end="", flush=True)
                time.sleep(1)
            print("\n✅ Wait complete, attempting download...")
    
    def record_success(self):
        """Record successful request"""
        self.last_request_time = datetime.now()
        self.consecutive_failures = 0
        self.current_delay = self.base_delay
        self.save_rate_limit_state()
        print("✅ Request successful - rate limit state reset")
    
    def record_failure(self, error_msg):
        """Record failed request and increase delay"""
        self.last_request_time = datetime.now()
        self.consecutive_failures += 1
        
        # Exponential backoff with jitter
        self.current_delay = min(
            self.base_delay * (self.backoff_multiplier ** self.consecutive_failures),
            self.max_delay
        )
        
        # Add random jitter (±20%)
        jitter = random.uniform(0.8, 1.2)
        self.current_delay = int(self.current_delay * jitter)
        
        self.save_rate_limit_state()
        
        print(f"❌ Request failed: {error_msg}")
        print(f"📈 Increased delay to {self.current_delay}s (failure #{self.consecutive_failures})")
        
        # Suggest next attempt time
        next_attempt = datetime.now() + timedelta(seconds=self.current_delay)
        print(f"🕐 Next attempt recommended at: {next_attempt.strftime('%H:%M:%S')}")
    
    def is_rate_limit_error(self, error_msg):
        """Check if error is rate limiting related"""
        rate_limit_indicators = [
            "401 Unauthorized",
            "403 Forbidden", 
            "Please wait a few minutes",
            "rate limit",
            "too many requests",
            "temporarily blocked"
        ]
        
        error_lower = error_msg.lower()
        return any(indicator.lower() in error_lower for indicator in rate_limit_indicators)
    
    def extract_shortcode(self, url):
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
    
    def download_reel(self, url):
        """Download Instagram reel with smart rate limiting"""
        
        shortcode = self.extract_shortcode(url)
        if not shortcode:
            print(f"❌ Could not extract shortcode from: {url}")
            return None
        
        print(f"📥 Smart downloading reel: {shortcode}")
        
        # Wait if rate limiting is active
        self.wait_if_needed()
        
        try:
            # Create Instaloader instance (same as working version)
            L = instaloader.Instaloader(
                dirname_pattern=str(self.output_dir),
                filename_pattern='{date_utc}_UTC',
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
            )
            
            print("🔍 Fetching post information...")
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            print(f"📹 Found post by: @{post.owner_username}")
            
            if not post.is_video:
                print(f"❌ Post {shortcode} is not a video")
                return None
            
            print("⬇️  Downloading video...")
            L.download_post(post, target=shortcode)
            
            # Find downloaded file (same logic as working version)
            video_files = list(self.output_dir.glob("*.mp4"))
            
            if not video_files:
                output_path = self.output_dir / shortcode
                if output_path.exists():
                    video_files = list(output_path.glob("*.mp4"))
            
            if video_files:
                video_file = video_files[0]
                
                # Clean up and rename
                if video_file.parent != self.output_dir:
                    clean_video_path = self.output_dir / f"{shortcode}.mp4"
                    import shutil
                    shutil.move(str(video_file), str(clean_video_path))
                    
                    if video_file.parent.is_dir():
                        shutil.rmtree(video_file.parent)
                    
                    video_file = clean_video_path
                else:
                    clean_video_path = self.output_dir / f"{shortcode}_{video_file.name}"
                    import shutil
                    shutil.move(str(video_file), str(clean_video_path))
                    video_file = clean_video_path
                
                file_size = os.path.getsize(video_file) / (1024 * 1024)
                print(f"✅ Downloaded: {video_file} ({file_size:.2f} MB)")
                
                # Record success
                self.record_success()
                
                return video_file
            else:
                print(f"❌ Video file not found for {shortcode}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            
            if self.is_rate_limit_error(error_msg):
                self.record_failure(error_msg)
                print(f"🔄 This appears to be rate limiting. Try again later or use longer delays.")
            else:
                print(f"❌ Download failed: {error_msg}")
            
            return None

def main():
    if len(sys.argv) < 2:
        print("🎬 Smart Rate Limit Instagram Downloader")
        print("=" * 50)
        print("\nUsage:")
        print("python smart_rate_limit_downloader.py <instagram_url>")
        print("\nExample:")
        print("python smart_rate_limit_downloader.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        print("\nFeatures:")
        print("- Intelligent rate limit detection")
        print("- Exponential backoff with jitter")
        print("- Persistent state across runs")
        print("- Same proven download method that worked this morning")
        return
    
    url = sys.argv[1]
    
    print("🚀 Smart Rate Limit Instagram Downloader")
    print("=" * 60)
    
    downloader = SmartRateLimitDownloader()
    result = downloader.download_reel(url)
    
    if result:
        print(f"\n🎉 Success! Downloaded: {result}")
        print("\n💡 Rate limiting handled successfully!")
    else:
        print("\n❌ Download failed")
        print("\n💡 If rate limited, the system will automatically wait longer next time.")

if __name__ == "__main__":
    main()