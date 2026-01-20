#!/usr/bin/env python3
"""
Batch Instagram Reel Transcriber
Reads URLs from file and performs: Download → Extract Audio → Transcribe to English
"""

import os
import sys
import ssl
import time
import shutil
import certifi
import urllib3
import requests
import json
import re
import instaloader
from pathlib import Path
from pydub import AudioSegment
import whisper
import tempfile
import random
from datetime import datetime, timedelta

# Import Instagrapi as fallback
try:
    from instagrapi import Client as InstagrapiClient
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False
    print("⚠️  Instagrapi not available - only Instaloader will be used")

# Import yt-dlp as final fallback
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("⚠️  yt-dlp not available")

# Import insta-scrape as additional fallback
try:
    import insta_scrape
    INSTASCRAPE_AVAILABLE = True
except ImportError:
    INSTASCRAPE_AVAILABLE = False
    print("⚠️  insta-scrape not available")

# Import parth-dl as additional fallback
try:
    import parth_dl
    PARTHDL_AVAILABLE = True
except ImportError:
    PARTHDL_AVAILABLE = False
    print("⚠️  parth-dl not available")

# Apply SSL fixes for corporate networks
def setup_ssl_bypass():
    """Apply aggressive SSL bypass for corporate networks"""
    print("🔧 Applying SSL bypass for corporate networks...")
    
    # 1. Disable all SSL verification
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # 2. Disable urllib3 warnings
    urllib3.disable_warnings()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)
    
    # 3. Set environment variables
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    # 4. Monkey patch requests to ignore SSL
    original_request = requests.Session.request
    
    def patched_request(self, method, url, **kwargs):
        kwargs['verify'] = False
        return original_request(self, method, url, **kwargs)
    
    requests.Session.request = patched_request
    
    # 5. Patch urllib3 SSL context
    from urllib3.util.ssl_ import create_urllib3_context
    
    def create_insecure_context():
        context = ssl.SSLContext()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    urllib3.util.ssl_.create_urllib3_context = create_insecure_context
    
    print("✅ SSL bypass applied (works with Zscaler and corporate proxies)")

class BatchInstagramTranscriber:
    def __init__(self, output_dir="batch_output", whisper_model="base"):
        """Initialize batch transcriber with smart rate limiting"""
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.videos_dir = self.output_dir / "videos"
        self.audio_dir = self.output_dir / "audio"
        self.transcripts_dir = self.output_dir / "transcripts"
        
        for dir_path in [self.videos_dir, self.audio_dir, self.transcripts_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Setup SSL bypass
        setup_ssl_bypass()
        
        # Initialize Whisper
        print(f"🤖 Loading Whisper {whisper_model} model...")
        self.whisper_model = whisper.load_model(whisper_model)
        
        # Initialize Instagrapi client as fallback
        if INSTAGRAPI_AVAILABLE:
            self.instagrapi_client = InstagrapiClient()
            print("✅ Instagrapi fallback initialized")
        else:
            self.instagrapi_client = None
        
        if YTDLP_AVAILABLE:
            print("✅ yt-dlp fallback available")
        
        if PARTHDL_AVAILABLE:
            print("✅ parth-dl fallback available")
        
        # Smart rate limiting
        self.rate_limit_file = Path("instagram_rate_limit.json")
        self.base_delay = 300  # Start with 5 minutes for Instagram
        self.max_delay = 7200  # Max 2 hours
        self.load_rate_limit_state()
        
        print("✅ Batch transcriber with smart rate limiting initialized")
    
    def load_rate_limit_state(self):
        """Load rate limiting state"""
        if self.rate_limit_file.exists():
            try:
                with open(self.rate_limit_file, 'r') as f:
                    data = json.load(f)
                    from datetime import datetime
                    self.last_request_time = datetime.fromisoformat(data.get('last_request_time', '2000-01-01'))
                    self.consecutive_failures = data.get('consecutive_failures', 0)
                    self.current_delay = data.get('current_delay', self.base_delay)
            except:
                self.reset_rate_limit_state()
        else:
            self.reset_rate_limit_state()
    
    def reset_rate_limit_state(self):
        """Reset rate limiting state"""
        from datetime import datetime
        self.last_request_time = datetime.min
        self.consecutive_failures = 0
        self.current_delay = self.base_delay
    
    def save_rate_limit_state(self):
        """Save rate limiting state"""
        import json
        from datetime import datetime
        data = {
            'last_request_time': self.last_request_time.isoformat(),
            'consecutive_failures': self.consecutive_failures,
            'current_delay': self.current_delay
        }
        with open(self.rate_limit_file, 'w') as f:
            json.dump(data, f)
    
    def should_wait_for_rate_limit(self):
        """Check if we should wait due to rate limiting"""
        from datetime import datetime
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        
        if self.consecutive_failures > 0:
            required_wait = self.current_delay
            if time_since_last < required_wait:
                wait_time = required_wait - time_since_last
                return True, wait_time
        
        return False, 0
    
    def handle_rate_limiting(self):
        """Handle rate limiting with smart delays"""
        should_wait, wait_time = self.should_wait_for_rate_limit()
        
        if should_wait:
            print(f"⏳ Instagram rate limit detected. Smart waiting {wait_time:.0f} seconds...")
            print(f"📊 Consecutive failures: {self.consecutive_failures}")
            print(f"🕐 Current delay: {self.current_delay}s")
            
            # Show progress
            import time
            for remaining in range(int(wait_time), 0, -60):  # Show every minute
                mins = remaining // 60
                secs = remaining % 60
                print(f"⏱️  Waiting: {mins}m {secs}s remaining...")
                time.sleep(min(60, remaining))
            
            print("✅ Wait complete, attempting download...")
    
    def record_download_success(self):
        """Record successful download"""
        from datetime import datetime
        self.last_request_time = datetime.now()
        self.consecutive_failures = 0
        self.current_delay = self.base_delay
        self.save_rate_limit_state()
    
    def record_download_failure(self, error_msg):
        """Record failed download and increase delay"""
        from datetime import datetime
        import random
        
        self.last_request_time = datetime.now()
        
        # Check if it's a rate limit error
        rate_limit_indicators = [
            "401 Unauthorized",
            "403 Forbidden", 
            "Please wait a few minutes",
            "rate limit",
            "too many requests"
        ]
        
        is_rate_limit = any(indicator.lower() in error_msg.lower() for indicator in rate_limit_indicators)
        
        if is_rate_limit:
            self.consecutive_failures += 1
            
            # Exponential backoff with jitter
            self.current_delay = min(
                self.base_delay * (2 ** self.consecutive_failures),
                self.max_delay
            )
            
            # Add random jitter (±20%)
            jitter = random.uniform(0.8, 1.2)
            self.current_delay = int(self.current_delay * jitter)
            
            self.save_rate_limit_state()
            
            print(f"📈 Rate limit detected. Increased delay to {self.current_delay}s (failure #{self.consecutive_failures})")
            
            # Suggest when to try again
            from datetime import datetime, timedelta
            next_attempt = datetime.now() + timedelta(seconds=self.current_delay)
            print(f"🕐 Recommended next attempt: {next_attempt.strftime('%H:%M:%S')}")
        else:
            print(f"❌ Non-rate-limit error: {error_msg}")
        
        return is_rate_limit
    
    def extract_shortcode_from_url(self, url):
        """Extract shortcode from Instagram URL"""
        parts = url.strip().split('/')
        for i, part in enumerate(parts):
            if part in ['p', 'reel', 'tv'] and i + 1 < len(parts):
                return parts[i + 1].split('?')[0]
        return None
    
    def download_instagram_reel(self, url):
        """Download Instagram reel with smart rate limiting and multiple fallbacks"""
        
        shortcode = self.extract_shortcode_from_url(url)
        if not shortcode:
            print(f"❌ Could not extract shortcode from: {url}")
            return None
        
        print(f"📥 Downloading reel: {shortcode}")
        
        # Handle rate limiting
        self.handle_rate_limiting()
        
        # Try Instaloader first (original method)
        print("🔧 Trying method 1: Instaloader...")
        try:
            video_path = self._download_with_instaloader(shortcode)
            if video_path:
                print("✅ SUCCESS: Downloaded using Instaloader")
                self.record_download_success()
                return video_path
        except Exception as e:
            print(f"❌ Instaloader failed: {str(e)[:100]}...")
            error_msg = str(e)
            is_rate_limited = self.record_download_failure(error_msg)
            if is_rate_limited:
                print(f"🔄 Rate limited. Will wait longer next time.")
                return None
        
        # Fallback to Instagrapi if Instaloader fails
        if self.instagrapi_client:
            print("🔧 Trying method 2: Instagrapi...")
            video_path = self._download_with_instagrapi(shortcode)
            if video_path:
                print("✅ SUCCESS: Downloaded using Instagrapi")
                self.record_download_success()
                return video_path
            else:
                print("❌ Instagrapi failed")
        
        # Final fallback to yt-dlp
        if YTDLP_AVAILABLE:
            print("🔧 Trying method 3: yt-dlp...")
            video_path = self._download_with_ytdlp(shortcode)
            if video_path:
                print("✅ SUCCESS: Downloaded using yt-dlp")
                self.record_download_success()
                return video_path
            else:
                print("❌ yt-dlp failed")
        
        # Try parth-dl
        if PARTHDL_AVAILABLE:
            print("🔧 Trying method 4: parth-dl...")
            video_path = self._download_with_parthdl(shortcode)
            if video_path:
                print("✅ SUCCESS: Downloaded using parth-dl")
                self.record_download_success()
                return video_path
            else:
                print("❌ parth-dl failed")
        
        print(f"❌ All download methods failed for {shortcode}")
        return None
    
    def _download_with_instaloader(self, shortcode):
        """Download using Instaloader (original method)"""
        try:
            import instaloader
            
            # Create Instaloader instance
            L = instaloader.Instaloader(
                dirname_pattern=str(self.videos_dir),
                filename_pattern='{date_utc}_UTC',
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
            )
            
            # Get post from shortcode
            print("🔍 Fetching post information (Instaloader)...")
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            print(f"📹 Found post by: @{post.owner_username}")
            
            if not post.is_video:
                print(f"❌ Post {shortcode} is not a video")
                return None
            
            print("⬇️  Downloading video...")
            L.download_post(post, target=shortcode)
            
            # Find the downloaded video file - check both patterns
            video_files = list(self.videos_dir.glob("*.mp4"))
            
            if not video_files:
                # Check in subdirectory
                output_path = self.videos_dir / shortcode
                if output_path.exists():
                    video_files = list(output_path.glob("*.mp4"))
            
            if video_files:
                video_file = video_files[0]
                
                # If file is in subdirectory, move it to main videos directory
                if video_file.parent != self.videos_dir:
                    clean_video_path = self.videos_dir / f"{shortcode}.mp4"
                    shutil.move(str(video_file), str(clean_video_path))
                    
                    # Clean up leftover directory
                    if video_file.parent.is_dir():
                        shutil.rmtree(video_file.parent)
                    
                    video_file = clean_video_path
                else:
                    # Rename to include shortcode for clarity
                    clean_video_path = self.videos_dir / f"{shortcode}_{video_file.name}"
                    shutil.move(str(video_file), str(clean_video_path))
                    video_file = clean_video_path
                
                file_size = os.path.getsize(video_file) / (1024 * 1024)
                print(f"✅ Downloaded with Instaloader: {video_file} ({file_size:.2f} MB)")
                
                return video_file
            else:
                print(f"❌ Video file not found for {shortcode}")
                return None
                
        except Exception as e:
            print(f"❌ Instaloader failed for {shortcode}: {e}")
            return None
    
    def _download_with_instagrapi(self, shortcode):
        """Download using Instagrapi (fallback method)"""
        try:
            print("🔍 Fetching post information (Instagrapi)...")
            
            # Try without login first for public posts
            try:
                # Get media info without login
                media_pk = self.instagrapi_client.media_pk_from_code(shortcode)
                media_info = self.instagrapi_client.media_info(media_pk)
            except Exception as e:
                if "login_required" in str(e).lower():
                    print("🔐 Login required for Instagrapi - trying anonymous access...")
                    # Try to get basic info via web scraping
                    return self._download_with_web_scraping(shortcode)
                else:
                    raise e
            
            if media_info.media_type != 2:  # 2 = video
                print(f"❌ Post {shortcode} is not a video")
                return None
            
            print(f"📹 Found video by: @{media_info.user.username}")
            
            # Download video
            print("⬇️  Downloading video with Instagrapi...")
            video_path = self.instagrapi_client.video_download(media_pk, folder=str(self.videos_dir))
            
            if video_path and os.path.exists(video_path):
                # Rename to include shortcode
                clean_video_path = self.videos_dir / f"{shortcode}_{Path(video_path).name}"
                shutil.move(str(video_path), str(clean_video_path))
                
                file_size = os.path.getsize(clean_video_path) / (1024 * 1024)
                print(f"✅ Downloaded with Instagrapi: {clean_video_path} ({file_size:.2f} MB)")
                
                return clean_video_path
            else:
                print(f"❌ Video download failed for {shortcode}")
                return None
                
        except Exception as e:
            print(f"❌ Instagrapi failed for {shortcode}: {e}")
            return None
    
    def _download_with_web_scraping(self, shortcode):
        """Fallback web scraping method"""
        try:
            print("🌐 Trying web scraping method...")
            
            # Create a session with headers
            session = requests.Session()
            session.verify = False
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
            
            # Get Instagram page
            url = f"https://www.instagram.com/p/{shortcode}/"
            response = session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch page: {response.status_code}")
                return None
            
            html_content = response.text
            
            # Look for video URL patterns
            video_patterns = [
                r'"video_url":"([^"]+)"',
                r'"videoUrl":"([^"]+)"',
                r'contentUrl":"([^"]+\.mp4[^"]*)"',
                r'"src":"([^"]+\.mp4[^"]*)"',
                r'video_url&quot;:&quot;([^&]+)&quot;'
            ]
            
            video_url = None
            for pattern in video_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    video_url = matches[0].replace('\\u0026', '&').replace('\\/', '/').replace('&amp;', '&')
                    break
            
            if not video_url:
                print(f"❌ Could not find video URL in page content")
                return None
            
            print(f"🎬 Found video URL via web scraping")
            
            # Download the video
            video_response = session.get(video_url, timeout=60, stream=True)
            
            if video_response.status_code != 200:
                print(f"❌ Failed to download video: {video_response.status_code}")
                return None
            
            # Save video file
            video_path = self.videos_dir / f"{shortcode}_webscrape.mp4"
            
            with open(video_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            print(f"✅ Downloaded via web scraping: {video_path} ({file_size:.2f} MB)")
            
            return video_path
            
        except Exception as e:
            print(f"❌ Web scraping failed for {shortcode}: {e}")
            return None
    
    def _download_with_ytdlp(self, shortcode):
        """Final fallback using yt-dlp"""
        try:
            print("🎬 Trying yt-dlp method...")
            
            url = f"https://www.instagram.com/p/{shortcode}/"
            
            # Configure yt-dlp options
            ydl_opts = {
                'outtmpl': str(self.videos_dir / f'{shortcode}_ytdlp.%(ext)s'),
                'format': 'best[ext=mp4]',
                'no_warnings': True,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    print(f"❌ Could not extract info for {shortcode}")
                    return None
                
                print(f"📹 Found video: {info.get('title', 'Unknown')}")
                
                # Download
                ydl.download([url])
                
                # Find downloaded file
                video_files = list(self.videos_dir.glob(f"{shortcode}_ytdlp.*"))
                
                if video_files:
                    video_file = video_files[0]
                    file_size = os.path.getsize(video_file) / (1024 * 1024)
                    print(f"✅ Downloaded with yt-dlp: {video_file} ({file_size:.2f} MB)")
                    return video_file
                else:
                    print(f"❌ yt-dlp download file not found")
                    return None
                    
        except Exception as e:
            print(f"❌ yt-dlp failed for {shortcode}: {e}")
            return None
    
    def _download_with_instascrape(self, shortcode):
        """Fallback using insta-scrape"""
        try:
            print("📸 Trying insta-scrape method...")
            
            url = f"https://www.instagram.com/p/{shortcode}/"
            
            # Use insta-scrape
            import insta_scrape
            
            post_data = insta_scrape.scrape_post(url)
            
            if not post_data or 'video_url' not in post_data:
                print(f"❌ No video found with insta-scrape for {shortcode}")
                return None
            
            video_url = post_data['video_url']
            print(f"🎬 Found video URL with insta-scrape")
            
            # Download the video
            response = requests.get(video_url, stream=True, verify=False)
            
            if response.status_code != 200:
                print(f"❌ Failed to download video: {response.status_code}")
                return None
            
            # Save video file
            video_path = self.videos_dir / f"{shortcode}_instascrape.mp4"
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            print(f"✅ Downloaded with insta-scrape: {video_path} ({file_size:.2f} MB)")
            
            return video_path
            
        except Exception as e:
            print(f"❌ insta-scrape failed for {shortcode}: {e}")
            return None
    
    def _download_with_parthdl(self, shortcode):
        """Fallback using parth-dl"""
        try:
            print("🚀 Trying parth-dl method...")
            
            url = f"https://www.instagram.com/p/{shortcode}/"
            
            # Use parth-dl
            import parth_dl
            
            # Configure parth-dl
            output_path = str(self.videos_dir / f"{shortcode}_parthdl.%(ext)s")
            
            # Download with parth-dl
            result = parth_dl.download(url, output_path)
            
            if result:
                # Find downloaded file
                video_files = list(self.videos_dir.glob(f"{shortcode}_parthdl.*"))
                
                if video_files:
                    video_file = video_files[0]
                    file_size = os.path.getsize(video_file) / (1024 * 1024)
                    print(f"✅ Downloaded with parth-dl: {video_file} ({file_size:.2f} MB)")
                    return video_file
                else:
                    print(f"❌ parth-dl download file not found")
                    return None
            else:
                print(f"❌ parth-dl download failed")
                return None
                
        except Exception as e:
            print(f"❌ parth-dl failed for {shortcode}: {e}")
            return None
    
    def extract_audio(self, video_path):
        """Extract audio from video"""
        
        video_path = Path(video_path)
        audio_path = self.audio_dir / f"{video_path.stem}.mp3"
        
        print(f"🎵 Extracting audio: {video_path.name} → {audio_path.name}")
        
        try:
            audio = AudioSegment.from_file(str(video_path))
            audio.export(
                str(audio_path),
                format="mp3",
                bitrate="192k",
                parameters=["-ac", "1"]  # Mono for better transcription
            )
            
            duration = len(audio) / 1000
            file_size = os.path.getsize(audio_path) / (1024 * 1024)
            
            print(f"✅ Audio extracted: {file_size:.2f}MB, {duration:.1f}s")
            return audio_path
            
        except Exception as e:
            print(f"❌ Audio extraction failed: {e}")
            return None
    
    def transcribe_to_english(self, audio_path):
        """Transcribe audio to English"""
        
        audio_path = Path(audio_path)
        transcript_path = self.transcripts_dir / f"{audio_path.stem}_transcript.txt"
        
        print(f"🎤 Transcribing to English: {audio_path.name}")
        
        try:
            # Convert to WAV if needed
            if audio_path.suffix.lower() == '.mp3':
                audio = AudioSegment.from_mp3(str(audio_path))
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    audio.export(temp_wav.name, format='wav')
                    wav_path = temp_wav.name
            else:
                wav_path = str(audio_path)
            
            try:
                # Detect language first
                detect_result = self.whisper_model.transcribe(wav_path, language=None, verbose=False)
                detected_lang = detect_result['language']
                
                print(f"📝 Detected language: {detected_lang}")
                
                # Transcribe/translate to English
                if detected_lang != 'en':
                    print("🔄 Translating to English...")
                    task = 'translate'
                else:
                    print("📝 Transcribing in English...")
                    task = 'transcribe'
                
                result = self.whisper_model.transcribe(
                    wav_path,
                    language=detected_lang,
                    task=task,
                    verbose=False,
                    temperature=0.0,
                    best_of=5,
                    beam_size=5
                )
                
                # Save transcript
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write("🎤 Instagram Reel Transcript (English)\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"📁 Source: {audio_path.name}\n")
                    f.write(f"🌍 Original Language: {detected_lang}\n")
                    f.write(f"🔄 Translated to English: {'Yes' if detected_lang != 'en' else 'No'}\n")
                    f.write(f"⏱️  Duration: {len(result['segments'])} segments\n\n")
                    
                    f.write("📝 Full Transcript:\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{result['text']}\n\n")
                    
                    f.write("🕐 Segments with Timestamps:\n")
                    f.write("-" * 40 + "\n")
                    for segment in result['segments']:
                        start = segment['start']
                        end = segment['end']
                        text = segment['text'].strip()
                        f.write(f"[{start:6.2f}s - {end:6.2f}s]: {text}\n")
                
                print(f"✅ Transcript saved: {transcript_path}")
                return transcript_path, result['text']
                
            finally:
                # Clean up temp WAV file
                if wav_path != str(audio_path) and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None, None
    
    def process_single_url(self, url, index=None, total=None):
        """Process a single Instagram URL through the complete pipeline"""
        
        prefix = f"[{index}/{total}] " if index and total else ""
        print(f"\n{prefix}🚀 Processing: {url}")
        print("=" * 60)
        
        # Step 1: Download
        video_path = self.download_instagram_reel(url)
        if not video_path:
            return {"url": url, "success": False, "error": "Download failed"}
        
        # Step 2: Extract Audio
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return {"url": url, "success": False, "error": "Audio extraction failed"}
        
        # Step 3: Transcribe
        transcript_path, transcript_text = self.transcribe_to_english(audio_path)
        if not transcript_path:
            return {"url": url, "success": False, "error": "Transcription failed"}
        
        return {
            "url": url,
            "success": True,
            "video_path": video_path,
            "audio_path": audio_path,
            "transcript_path": transcript_path,
            "transcript_text": transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text
        }
    
    def process_urls_from_file(self, urls_file, delay_between=5):
        """Process multiple URLs from a file"""
        
        urls_file = Path(urls_file)
        
        if not urls_file.exists():
            print(f"❌ URLs file not found: {urls_file}")
            return []
        
        # Read URLs from file
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not urls:
            print(f"❌ No valid URLs found in {urls_file}")
            return []
        
        print(f"📋 Found {len(urls)} URLs to process")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏱️  Delay between downloads: {delay_between}s")
        
        results = []
        
        for i, url in enumerate(urls, 1):
            result = self.process_single_url(url, i, len(urls))
            results.append(result)
            
            if result['success']:
                print(f"✅ Completed: {result['transcript_text']}")
            else:
                print(f"❌ Failed: {result['error']}")
            
            # Delay between requests to avoid rate limiting
            if i < len(urls):
                print(f"⏳ Waiting {delay_between}s before next download...")
                time.sleep(delay_between)
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results):
        """Generate a summary report of all processed URLs"""
        
        report_path = self.output_dir / "batch_summary.txt"
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("🎤 Batch Instagram Transcription Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"📊 Total URLs: {len(results)}\n")
            f.write(f"✅ Successful: {len(successful)}\n")
            f.write(f"❌ Failed: {len(failed)}\n")
            f.write(f"📈 Success Rate: {len(successful)/len(results)*100:.1f}%\n\n")
            
            if successful:
                f.write("✅ Successful Transcriptions:\n")
                f.write("-" * 40 + "\n")
                for i, result in enumerate(successful, 1):
                    f.write(f"{i}. {result['url']}\n")
                    f.write(f"   📄 Transcript: {result['transcript_path']}\n")
                    f.write(f"   📝 Preview: {result['transcript_text']}\n\n")
            
            if failed:
                f.write("❌ Failed URLs:\n")
                f.write("-" * 20 + "\n")
                for i, result in enumerate(failed, 1):
                    f.write(f"{i}. {result['url']}\n")
                    f.write(f"   Error: {result['error']}\n\n")
        
        print(f"\n📊 Summary report saved: {report_path}")
        print(f"✅ Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("🎤 Batch Instagram Reel Transcriber")
        print("=" * 40)
        print("\nUsage:")
        print("python batch_instagram_transcriber.py <urls_file> [options]")
        print("\nOptions:")
        print("  --output DIR     Output directory (default: batch_output)")
        print("  --model SIZE     Whisper model size (default: base)")
        print("  --delay SECONDS  Delay between downloads (default: 5)")
        print("\nURL File Format:")
        print("  One Instagram URL per line")
        print("  Lines starting with # are ignored")
        print("\nExample:")
        print("python batch_instagram_transcriber.py urls.txt --output results --model large")
        print("\nExample urls.txt:")
        print("# Instagram reels to transcribe")
        print("https://www.instagram.com/reel/ABC123/")
        print("https://www.instagram.com/reel/XYZ789/")
        return
    
    urls_file = sys.argv[1]
    
    # Parse options
    output_dir = "batch_output"
    model_size = "base"
    delay = 5
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--model" and i + 1 < len(sys.argv):
            model_size = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--delay" and i + 1 < len(sys.argv):
            delay = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    print("🚀 Batch Instagram Reel Transcriber")
    print("=" * 50)
    print(f"📁 URLs file: {urls_file}")
    print(f"📂 Output directory: {output_dir}")
    print(f"🤖 Whisper model: {model_size}")
    print(f"⏱️  Delay between downloads: {delay}s")
    
    # Initialize and run
    transcriber = BatchInstagramTranscriber(output_dir, model_size)
    results = transcriber.process_urls_from_file(urls_file, delay)
    
    print(f"\n🎉 Batch processing completed!")
    print(f"📊 Check {output_dir}/batch_summary.txt for detailed results")

if __name__ == "__main__":
    main()