# Audio-to-Text Transcription Tool

High-accuracy speech recognition for Hindi, English, and Hinglish audio using OpenAI Whisper.

**✅ Bonus: Instagram Reel Downloader with Corporate Network SSL Bypass**

## 🚀 Quick Start

# Instagram Reel Batch Transcriber

Complete automation tool for Instagram reel transcription with multiple download methods and smart rate limiting.

**✅ NEW: Multiple Download Methods + Smart Rate Limiting**

## 🚀 Quick Start

### For Batch Processing (Recommended):
```bash
# 1. Create URLs file
echo "https://www.instagram.com/reel/DTBkPhSk63f/" > urls.txt

# 2. Run complete pipeline (Download → Extract → Transcribe)
source venv/bin/activate
python batch_instagram_transcriber.py urls.txt

# 3. Check results in batch_output/ folder
```

### For Single Downloads:
```bash
# Try the most reliable method first
python downloaders/aggressive_ssl_bypass.py "https://www.instagram.com/reel/DTBkPhSk63f/"

# If rate limited, try smart rate limiter
python downloaders/smart_rate_limit_downloader.py "https://www.instagram.com/reel/DTBkPhSk63f/"
```

## 📋 Features

- ✅ **9 Different Download Methods** - Multiple fallbacks for maximum reliability
- ✅ **Smart Rate Limiting** - Handles Instagram's rate limits intelligently  
- ✅ **Batch Processing** - Process multiple URLs automatically
- ✅ **Complete Pipeline** - Download → Extract Audio → Transcribe in one command
- ✅ **English Translation** - Converts Hindi/Hinglish to readable English
- ✅ **Corporate Network Support** - Bypasses SSL restrictions (Zscaler, etc.)
- ✅ **Organized Output** - Separate folders for videos, audio, transcripts
- ✅ **Progress Tracking** - Real-time status and detailed logging
- ✅ **Error Recovery** - Continues processing even if some URLs fail

## 🎯 Download Methods (Best to Worst)

1. **aggressive_ssl_bypass.py** ⭐ - Proven working method (100% success this morning)
2. **smart_rate_limit_downloader.py** 🧠 - Intelligent rate limiting with exponential backoff
3. **selenium_instagram_downloader.py** 🤖 - Real browser automation
4. **simple_instaloader.py** - Basic instaloader with SSL bypass
5. **ytdlp_method.py** - Popular yt-dlp tool
6. **instagrapi_method.py** - Instagram API wrapper
7. **gallery_dl_method.py** - Multi-site downloader
8. **api_instagram_downloader.py** - Third-party APIs
9. **instagram_browser_downloader.py** - Browser-style requests

See `downloaders/README.md` for detailed information on each method.

## 🛠 Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 💡 Usage Examples

### Batch Processing with Smart Rate Limiting:
```bash
# Create URLs file
cat > urls.txt << EOF
https://www.instagram.com/reel/DTBkPhSk63f/
https://www.instagram.com/reel/ANOTHER_SHORTCODE/
EOF

# Run with smart rate limiting (recommended)
python batch_instagram_transcriber.py urls.txt --model base --delay 300

# Check results
ls batch_output/
```

### Advanced Options:
```bash
# Custom output directory and model
python batch_instagram_transcriber.py urls.txt --output my_results --model medium --delay 600

# Quick processing (if not rate limited)
python batch_instagram_transcriber.py urls.txt --model base --delay 60
```

### Individual Steps:
```bash
# 1. Download only
python downloaders/aggressive_ssl_bypass.py "URL"

# 2. Convert to audio
python mp4_to_audio.py

# 3. Transcribe with multiple formats
python improved_transcriber.py
```

## 📋 Features

- ✅ **Batch Processing** - Process multiple Instagram URLs automatically
- ✅ **Complete Pipeline** - Download → Extract Audio → Transcribe in one command
- ✅ **English Translation** - Converts Hindi/Hinglish to readable English
- ✅ **High accuracy** for Hindi, English, and Hinglish
- ✅ **Automatic language detection**
- ✅ **Timestamp support** (word-level timing)
- ✅ **Multiple model sizes** (tiny to large)
- ✅ **Offline processing** (no internet required after setup)
- ✅ **Mixed language support** (code-switching)
- ✅ **Instagram reel download** (bypasses Zscaler/corporate proxies)
- ✅ **Organized output** (separate folders for videos, audio, transcripts)
- ✅ **Progress tracking** with detailed logging
- ✅ **Error handling** (continues processing even if some URLs fail)

## 🎯 Model Recommendations

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| `tiny` | Fastest | Basic | Quick testing |
| `base` | Fast | Good | General use (recommended) |
| `small` | Medium | Better | Important files |
| `medium` | Slow | High | Professional transcription |
| `large` | Slowest | Highest | Critical accuracy needed |

## 💡 Usage Examples

### Batch Instagram Processing (Complete Automation):
```bash
# 1. Create URLs file
echo "https://www.instagram.com/reel/DTBkPhSk63f/" > urls.txt
echo "https://www.instagram.com/reel/ANOTHER_SHORTCODE/" >> urls.txt

# 2. Run complete pipeline
python batch_instagram_transcriber.py urls.txt --output results --model large

# 3. Check results in results/ folder
```

### Advanced Batch Options:
```bash
# Custom output directory and model
python batch_instagram_transcriber.py urls.txt --output my_results --model large --delay 10

# Quick processing with base model
python batch_instagram_transcriber.py urls.txt --model base --delay 2
```

### Single Instagram Reel (Manual Steps):
```bash
# 1. Download Instagram reel
python aggressive_ssl_bypass.py "https://www.instagram.com/reel/DTBkPhSk63f/"

# 2. Convert to audio (if needed)
python mp4_to_audio.py

# 3. Transcribe with multiple formats
python improved_transcriber.py
```

### Basic Audio Transcription:
```python
from whisper_transcriber import MultilingualTranscriber

# Initialize with base model
transcriber = MultilingualTranscriber(model_size="base")

# Transcribe audio file
result = transcriber.transcribe_mp3("audio.mp3")
print(result['text'])
```

### With Language Hint:
```python
# Force Hindi detection
result = transcriber.transcribe_mp3("audio.mp3", language="hi")

# Force English detection  
result = transcriber.transcribe_mp3("audio.mp3", language="en")
```

## 🔧 Command Line Usage

```bash
# Direct Whisper CLI (after activation)
whisper audio.mp3 --model base --language hi
whisper audio.mp3 --model large --task translate  # Translate to English
```

## 🎵 Supported Audio Formats

- MP3 (primary)
- WAV
- M4A
- FLAC
- Any format supported by pydub

## 🌟 Why This Solution Works

### For Transcription:
1. **Multilingual Training**: Trained on diverse Hindi content
2. **Code-switching**: Handles English-Hindi mixing naturally
3. **Robust**: Works with various accents and audio quality
4. **Open Source**: No API costs or usage limits
5. **Offline**: Complete privacy, no data sent to servers

### For Instagram Downloads:
1. **SSL Bypass**: Successfully bypasses Zscaler and corporate proxies
2. **Automatic Audio Extraction**: Converts video to MP3 automatically
3. **Clean Output**: Saves only the audio file for transcription
4. **Corporate Network Compatible**: Works in restricted environments

## 🛠 Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🛠 Troubleshooting

### Common Issues:

1. **"No module named 'whisper'"**
   ```bash
   source venv/bin/activate
   pip install openai-whisper
   ```

2. **SSL Certificate errors (Instagram download)**
   - The `aggressive_ssl_bypass.py` should handle this automatically
   - If still failing, try from a different network

3. **Audio format errors**
   ```bash
   pip install pydub
   # Install ffmpeg: brew install ffmpeg (macOS)
   ```

4. **Memory issues with large models**
   - Use smaller models (base/small)
   - Process shorter audio segments

## 📊 Performance Tips

- **Audio Quality**: Clean, clear audio = better results
- **File Length**: Break long files into chunks (< 30 minutes)
- **Model Selection**: Start with 'base', upgrade if needed
- **Language Hints**: Use when you know the primary language
- **Corporate Networks**: Use `aggressive_ssl_bypass.py` for Instagram downloads

Ready to transcribe! 🎉