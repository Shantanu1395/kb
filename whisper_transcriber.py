#!/usr/bin/env python3
"""
High-accuracy Hindi/English/Hinglish Speech-to-Text using Whisper
"""

import whisper
import os
from pydub import AudioSegment
import tempfile
from pathlib import Path

class MultilingualTranscriber:
    def __init__(self, model_size="base"):
        """
        Initialize Whisper model
        model_size options: tiny, base, small, medium, large
        - tiny: fastest, lowest accuracy
        - base: good balance (recommended for testing)
        - large: highest accuracy, slower
        """
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        
    def transcribe_mp3(self, mp3_path, language=None, force_english_output=False):
        """
        Transcribe MP3 file to text with improved accuracy for Hindi/English mix
        
        Args:
            mp3_path: Path to MP3 file
            language: Optional language hint ('hi' for Hindi, 'en' for English, None for auto-detect)
            force_english_output: If True, translates to English; if False, keeps original language
        
        Returns:
            dict with transcription results
        """
        if not os.path.exists(mp3_path):
            raise FileNotFoundError(f"MP3 file not found: {mp3_path}")
            
        print(f"Transcribing: {mp3_path}")
        
        # Whisper works best with WAV files, convert if needed
        if mp3_path.lower().endswith('.mp3'):
            audio = AudioSegment.from_mp3(mp3_path)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                audio.export(temp_wav.name, format='wav')
                wav_path = temp_wav.name
        else:
            wav_path = mp3_path
            
        try:
            # First, detect the language without forcing any specific language
            print("🔍 Detecting language...")
            detect_result = self.model.transcribe(wav_path, language=None, verbose=False)
            detected_lang = detect_result['language']
            
            print(f"📝 Detected language: {detected_lang}")
            
            # Choose transcription strategy based on detected language and user preference
            if force_english_output and detected_lang != 'en':
                print("🔄 Translating to English...")
                task = 'translate'  # Translate to English
                final_language = detected_lang
            else:
                print("📝 Transcribing in original language...")
                task = 'transcribe'  # Keep original language
                final_language = detected_lang
            
            # Perform the actual transcription/translation
            result = self.model.transcribe(
                wav_path, 
                language=detected_lang,  # Use detected language for better accuracy
                task=task,
                verbose=True,
                # Additional options for better accuracy
                temperature=0.0,  # More deterministic output
                best_of=5,       # Try multiple attempts for better accuracy
                beam_size=5,     # Use beam search for better results
            )
            
            return {
                'text': result['text'],
                'language': final_language,
                'original_language': detected_lang,
                'translated_to_english': force_english_output and detected_lang != 'en',
                'segments': result['segments']
            }
            
        finally:
            # Clean up temporary file
            if wav_path != mp3_path and os.path.exists(wav_path):
                os.unlink(wav_path)
    
    def transcribe_with_timestamps(self, mp3_path, language=None, force_english_output=False):
        """Get transcription with word-level timestamps"""
        result = self.transcribe_mp3(mp3_path, language, force_english_output)
        
        print(f"\nOriginal Language: {result['original_language']}")
        if result.get('translated_to_english'):
            print("✅ Translated to English")
        else:
            print("📝 Transcribed in original language")
        print(f"Full Text: {result['text']}")
        print("\nSegments with timestamps:")
        
        for segment in result['segments']:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}")
        
        # Save transcription to file
        self.save_transcription_to_file(mp3_path, result)
            
        return result
    
    def save_transcription_to_file(self, audio_path, result):
        """Save transcription results to a text file"""
        
        audio_path = Path(audio_path)
        output_file = audio_path.parent / f"{audio_path.stem}_transcription.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("🎤 Audio Transcription Results\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"📁 Source File: {audio_path.name}\n")
                f.write(f"🌍 Original Language: {result['original_language']}\n")
                
                if result.get('translated_to_english'):
                    f.write("🔄 Translated to English: Yes\n")
                else:
                    f.write("📝 Language: Original\n")
                
                f.write(f"⏱️  Duration: {len(result['segments'])} segments\n\n")
                
                f.write("📝 Full Transcription:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{result['text']}\n\n")
                
                f.write("🕐 Detailed Segments with Timestamps:\n")
                f.write("-" * 45 + "\n")
                for segment in result['segments']:
                    start_time = segment['start']
                    end_time = segment['end']
                    text = segment['text'].strip()
                    f.write(f"[{start_time:6.2f}s - {end_time:6.2f}s]: {text}\n")
            
            print(f"\n💾 Transcription saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"⚠️  Could not save transcription file: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Initialize transcriber
    transcriber = MultilingualTranscriber(model_size="base")
    
    # Get user input
    mp3_file = input("Enter path to audio file (MP3/MP4/WAV): ")
    
    if os.path.exists(mp3_file):
        try:
            # Ask user for transcription preference
            print("\n🎯 Transcription Options:")
            print("1. Keep original language (Hindi/English mix)")
            print("2. Translate everything to English")
            
            choice = input("Choose option (1 or 2): ").strip()
            
            force_english = choice == "2"
            
            if force_english:
                print("🔄 Will translate to English")
            else:
                print("📝 Will keep original language")
            
            result = transcriber.transcribe_with_timestamps(mp3_file, force_english_output=force_english)
            
            print(f"\n🎉 Transcription completed!")
            print(f"📊 Language: {result['original_language']}")
            print(f"📝 Segments: {len(result['segments'])}")
            print(f"📄 Text length: {len(result['text'])} characters")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ File not found!")