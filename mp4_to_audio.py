#!/usr/bin/env python3
"""
MP4 to Audio Converter
Converts MP4 video files to MP3 audio for transcription
"""

import os
import sys
from pathlib import Path
from pydub import AudioSegment

def convert_mp4_to_audio(video_path, output_path=None, audio_format="mp3", bitrate="192k"):
    """
    Convert MP4 video to audio file
    
    Args:
        video_path: Path to MP4 video file
        output_path: Optional output path (auto-generated if None)
        audio_format: Output format (mp3, wav, etc.)
        bitrate: Audio bitrate for MP3
    
    Returns:
        Path to converted audio file
    """
    
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Generate output path if not provided
    if output_path is None:
        output_path = video_path.with_suffix(f'.{audio_format}')
    else:
        output_path = Path(output_path)
    
    print(f"🎵 Converting {video_path.name} to audio...")
    print(f"📁 Input: {video_path}")
    print(f"📁 Output: {output_path}")
    
    try:
        # Load video file
        audio = AudioSegment.from_file(str(video_path))
        
        # Export as audio
        if audio_format.lower() == "mp3":
            audio.export(
                str(output_path),
                format="mp3",
                bitrate=bitrate,
                parameters=["-ac", "1"]  # Convert to mono for better transcription
            )
        else:
            audio.export(str(output_path), format=audio_format)
        
        # Get file size
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        duration = len(audio) / 1000  # Duration in seconds
        
        print(f"✅ Audio extracted successfully!")
        print(f"   📊 Size: {file_size:.2f} MB")
        print(f"   ⏱️  Duration: {duration:.1f} seconds")
        print(f"   🎧 Format: {audio_format.upper()}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None

def batch_convert(input_dir, output_dir=None, audio_format="mp3"):
    """Convert all MP4 files in a directory"""
    
    input_dir = Path(input_dir)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    else:
        output_dir = input_dir
    
    mp4_files = list(input_dir.glob("*.mp4"))
    
    if not mp4_files:
        print(f"❌ No MP4 files found in {input_dir}")
        return []
    
    print(f"🔄 Found {len(mp4_files)} MP4 files to convert")
    
    converted_files = []
    
    for video_file in mp4_files:
        output_file = output_dir / f"{video_file.stem}.{audio_format}"
        
        result = convert_mp4_to_audio(video_file, output_file, audio_format)
        
        if result:
            converted_files.append(result)
        
        print()  # Add spacing between conversions
    
    print(f"✅ Converted {len(converted_files)} files successfully")
    return converted_files

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("🎵 MP4 to Audio Converter")
        print("=" * 30)
        print("\nUsage:")
        print("python mp4_to_audio.py <video_file> [output_file]")
        print("python mp4_to_audio.py <directory> --batch")
        print("\nExamples:")
        print("python mp4_to_audio.py video.mp4")
        print("python mp4_to_audio.py video.mp4 audio.mp3")
        print("python mp4_to_audio.py downloads/ --batch")
        print("\nSupported formats: MP3, WAV, FLAC, M4A")
        return
    
    input_path = sys.argv[1]
    
    # Check for batch mode
    if len(sys.argv) > 2 and sys.argv[2] == "--batch":
        converted_files = batch_convert(input_path)
        
        if converted_files:
            print(f"\n🎤 Ready for transcription:")
            for file in converted_files:
                print(f"   python whisper_transcriber.py")
                print(f"   # Enter: {file}")
    else:
        # Single file conversion
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        result = convert_mp4_to_audio(input_path, output_path)
        
        if result:
            print(f"\n🎤 Next step - transcribe:")
            print(f"python whisper_transcriber.py")
            print(f"# Enter: {result}")

if __name__ == "__main__":
    main()