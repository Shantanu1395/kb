#!/usr/bin/env python3
"""
Improved Hindi/English/Hinglish Transcriber
Forces Roman script output for better readability
"""

import whisper
import os
import tempfile
from pydub import AudioSegment
from pathlib import Path

class ImprovedTranscriber:
    def __init__(self, model_size="base"):
        """Initialize with Whisper model"""
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
    
    def transcribe_audio(self, audio_path, output_format="english"):
        """
        Transcribe audio with different output formats
        
        Args:
            audio_path: Path to audio file
            output_format: "english" (translate to English), "roman" (Hindi in Roman script), "original" (original script)
        
        Returns:
            dict with transcription results
        """
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"🎤 Transcribing: {Path(audio_path).name}")
        print(f"📝 Output format: {output_format}")
        
        # Convert to WAV if needed
        if audio_path.lower().endswith('.mp3'):
            audio = AudioSegment.from_mp3(audio_path)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                audio.export(temp_wav.name, format='wav')
                wav_path = temp_wav.name
        else:
            wav_path = audio_path
        
        try:
            # Step 1: Detect language
            print("🔍 Detecting language...")
            detect_result = self.model.transcribe(wav_path, language=None, verbose=False)
            detected_lang = detect_result['language']
            print(f"📝 Detected language: {detected_lang}")
            
            # Step 2: Choose transcription strategy
            if output_format == "english":
                # Always translate to English
                print("🔄 Translating to English...")
                result = self.model.transcribe(
                    wav_path,
                    language=detected_lang,
                    task='translate',  # Translate to English
                    verbose=True,
                    temperature=0.0,
                    best_of=5,
                    beam_size=5
                )
                final_text = result['text']
                
            elif output_format == "roman":
                # For Hindi, force English transcription to get Roman script
                if detected_lang == 'hi':
                    print("🔄 Converting Hindi to Roman script...")
                    # Use English language setting to force Roman script
                    result = self.model.transcribe(
                        wav_path,
                        language='en',  # Force English to get Roman script
                        task='transcribe',
                        verbose=True,
                        temperature=0.0,
                        best_of=5,
                        beam_size=5
                    )
                else:
                    # For other languages, transcribe normally
                    result = self.model.transcribe(
                        wav_path,
                        language=detected_lang,
                        task='transcribe',
                        verbose=True,
                        temperature=0.0,
                        best_of=5,
                        beam_size=5
                    )
                final_text = result['text']
                
            else:  # original
                # Keep original language and script
                print("📝 Transcribing in original language...")
                result = self.model.transcribe(
                    wav_path,
                    language=detected_lang,
                    task='transcribe',
                    verbose=True,
                    temperature=0.0,
                    best_of=5,
                    beam_size=5
                )
                final_text = result['text']
            
            return {
                'text': final_text,
                'detected_language': detected_lang,
                'output_format': output_format,
                'segments': result['segments']
            }
            
        finally:
            # Clean up temp file
            if wav_path != audio_path and os.path.exists(wav_path):
                os.unlink(wav_path)
    
    def transcribe_with_all_formats(self, audio_path):
        """Transcribe with all three formats for comparison"""
        
        print("🎯 Transcribing with all output formats...")
        
        formats = {
            'english': 'English Translation',
            'roman': 'Roman Script (Hindi in English letters)',
            'original': 'Original Script'
        }
        
        results = {}
        
        for format_key, format_name in formats.items():
            print(f"\n{'='*50}")
            print(f"🔄 Format: {format_name}")
            print('='*50)
            
            try:
                result = self.transcribe_audio(audio_path, format_key)
                results[format_key] = result
                
                print(f"\n📝 Result ({format_name}):")
                print(f"Text: {result['text'][:200]}...")
                
            except Exception as e:
                print(f"❌ Failed for {format_name}: {e}")
                results[format_key] = None
        
        # Save all results to file
        self.save_all_results(audio_path, results)
        
        return results
    
    def save_all_results(self, audio_path, results):
        """Save all transcription results to file"""
        
        audio_path = Path(audio_path)
        output_file = audio_path.parent / f"{audio_path.stem}_all_transcriptions.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("🎤 Complete Audio Transcription Results\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"📁 Source File: {audio_path.name}\n")
                f.write(f"🌍 Detected Language: {results.get('english', {}).get('detected_language', 'Unknown')}\n\n")
                
                formats = {
                    'english': '🌍 English Translation',
                    'roman': '🔤 Roman Script (Hindi in English letters)',
                    'original': '📜 Original Script'
                }
                
                for format_key, format_title in formats.items():
                    f.write(f"{format_title}\n")
                    f.write("-" * 50 + "\n")
                    
                    if results.get(format_key):
                        result = results[format_key]
                        f.write(f"Full Text:\n{result['text']}\n\n")
                        
                        f.write("Segments with Timestamps:\n")
                        for segment in result['segments']:
                            start = segment['start']
                            end = segment['end']
                            text = segment['text'].strip()
                            f.write(f"[{start:6.2f}s - {end:6.2f}s]: {text}\n")
                    else:
                        f.write("❌ Transcription failed for this format\n")
                    
                    f.write("\n" + "="*60 + "\n\n")
            
            print(f"\n💾 All transcriptions saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
            return None

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("🎤 Improved Hindi/English/Hinglish Transcriber")
        print("=" * 50)
        print("\nUsage:")
        print("python improved_transcriber.py <audio_file> [format]")
        print("\nFormats:")
        print("  english  - Translate everything to English")
        print("  roman    - Hindi in Roman/English script")
        print("  original - Keep original script")
        print("  all      - Generate all three formats")
        print("\nExamples:")
        print("python improved_transcriber.py audio.mp3 english")
        print("python improved_transcriber.py audio.mp3 all")
        return
    
    audio_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        return
    
    transcriber = ImprovedTranscriber("base")
    
    if output_format == "all":
        results = transcriber.transcribe_with_all_formats(audio_file)
        
        print(f"\n🎉 Transcription completed!")
        print(f"📊 Generated {len([r for r in results.values() if r])} successful transcriptions")
        
    else:
        if output_format not in ['english', 'roman', 'original']:
            print(f"❌ Invalid format: {output_format}")
            print("Valid formats: english, roman, original, all")
            return
        
        result = transcriber.transcribe_audio(audio_file, output_format)
        
        print(f"\n🎉 Transcription completed!")
        print(f"📝 Format: {output_format}")
        print(f"🌍 Detected: {result['detected_language']}")
        print(f"📄 Text: {result['text']}")

if __name__ == "__main__":
    import sys
    main()