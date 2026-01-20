#!/usr/bin/env python3
"""
Instagram Reel Downloader with SSL Bypass for Corporate Networks
Successfully bypasses Zscaler and other corporate proxies
"""

import ssl
import os
import sys
import certifi
import urllib3
import requests
from urllib3.util.ssl_ import create_urllib3_context
from pathlib import Path

def aggressive_ssl_bypass():
    """Apply all possible SSL bypasses for corporate networks"""
    
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
    def create_insecure_context():
        context = ssl.SSLContext()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    urllib3.util.ssl_.create_urllib3_context = create_insecure_context
    
    print("✅ SSL bypass applied (works with Zscaler and corporate proxies)")

def download_instagram_reel(url_or_shortcode, output_dir="downloads"):
    """Download Instagram reel with SSL bypass"""
    
    # Apply SSL fixes first
    aggressive_ssl_bypass()
    
    # Extract shortcode from URL if needed
    if 'instagram.com' in url_or_shortcode:
        parts = url_or_shortcode.split('/')
        shortcode = None
        for i, part in enumerate(parts):
            if part in ['p', 'reel', 'tv'] and i + 1 < len(parts):
                shortcode = parts[i + 1].split('?')[0]  # Remove query parameters
                break
        
        if not shortcode:
            print("❌ Could not extract shortcode from URL")
            return None
    else:
        shortcode = url_or_shortcode
    
    print(f"📥 Downloading Instagram reel: {shortcode}")
    
    try:
        import instaloader
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
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
        print(f"📅 Date: {post.date}")
        print(f"🎥 Is Video: {post.is_video}")
        
        if post.is_video:
            print("⬇️  Downloading video...")
            L.download_post(post, target=shortcode)
            
            # Find the downloaded video file
            output_path = Path(output_dir) / shortcode
            video_files = list(output_path.glob("*.mp4"))
            
            if video_files:
                video_file = video_files[0]
                print(f"✅ Downloaded: {video_file}")
                
                # Extract audio using pydub
                try:
                    from pydub import AudioSegment
                    
                    print("🎵 Extracting audio...")
                    audio = AudioSegment.from_file(str(video_file))
                    
                    # Save audio in main downloads folder for easy access
                    mp3_file = Path(output_dir) / f"{shortcode}_audio.mp3"
                    audio.export(str(mp3_file), format="mp3", bitrate="192k")
                    
                    print(f"✅ Audio extracted: {mp3_file}")
                    
                    # Clean up video folder (keep only the MP3)
                    import shutil
                    shutil.rmtree(output_path)
                    
                    return mp3_file
                    
                except Exception as e:
                    print(f"⚠️  Audio extraction failed: {e}")
                    return video_file
            else:
                print("❌ Video file not found after download")
                return None
        else:
            print("❌ Post is not a video")
            return None
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        
        if "SSL" in str(e) or "certificate" in str(e).lower():
            print("\n🔍 Still getting SSL errors despite bypass.")
            print("💡 Try these alternatives:")
            print("   1. Use different network (personal WiFi/mobile hotspot)")
            print("   2. Use online tools: snapinsta.app")
            print("   3. Use browser extensions")
        
        return None

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("🎬 Instagram Reel Downloader with SSL Bypass")
        print("=" * 50)
        print("\n✅ Successfully bypasses corporate networks (Zscaler, etc.)")
        print("\nUsage:")
        print("python aggressive_ssl_bypass.py <instagram_url_or_shortcode>")
        print("\nExamples:")
        print("python aggressive_ssl_bypass.py DTBkPhSk63f")
        print("python aggressive_ssl_bypass.py 'https://www.instagram.com/reel/DTBkPhSk63f/'")
        print("\n🎤 After download, transcribe with:")
        print("python whisper_transcriber.py")
        return
    
    url_or_shortcode = sys.argv[1]
    
    print("🚀 Instagram Reel Downloader with Corporate Network SSL Bypass")
    print("=" * 70)
    
    result = download_instagram_reel(url_or_shortcode)
    
    if result:
        print(f"\n🎉 Success! Audio ready for transcription: {result}")
        print(f"\n🎤 Next step - transcribe:")
        print(f"python whisper_transcriber.py")
        print(f"# Enter path: {result}")
    else:
        print("\n❌ Download failed")
        print("\n💡 Alternative: Use manual download methods")

if __name__ == "__main__":
    main()