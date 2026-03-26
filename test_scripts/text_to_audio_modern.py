#!/usr/bin/env python3
"""
Modern Text-to-Audio Script
Converts terminal input text into natural-sounding audio using Microsoft Edge TTS.
Features multiple high-quality neural voices.
"""

import asyncio
import sys
import os
from pathlib import Path


async def detect_language_and_get_voice(text):
    """
    Detect if text contains Cyrillic characters (Bulgarian) and return appropriate voice.
    
    Returns:
        str: Voice identifier (Bulgarian or English)
    """
    # Check if text contains Cyrillic characters
    cyrillic_count = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    
    # If more than 20% of characters are Cyrillic, use Bulgarian voice
    if len(text) > 0 and cyrillic_count / len(text) > 0.2:
        return "bg-BG-BorislavNeural"  # Bulgarian male voice
    else:
        return "en-US-AriaNeural"  # English female voice


async def text_to_audio_and_play(text, voice=None, rate=1.0):
    """
    Convert text to audio using Edge TTS and play it.
    
    Args:
        text (str): The text to convert to audio
        voice (str): Voice identifier (e.g., 'en-US-AriaNeural', 'bg-BG-BorislavNeural'). 
                     If None, auto-detects language.
        rate (float): Speech rate multiplier (0.5 to 2.0)
    """
    try:
        import edge_tts
        
        # Auto-detect language if voice not specified
        if voice is None:
            voice = await detect_language_and_get_voice(text)
            print(f"Auto-detected voice: {voice}")
        
        # Validate and convert rate to string format
        rate = max(0.5, min(2.0, rate))
        rate_percent = int((rate - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%"
        
        print(f"Using voice: {voice}")
        print("Converting text to audio...")
        
        # Create temporary audio file
        audio_file = "temp_audio.mp3"
        
        # Create communicate object
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate_str)
        
        # Save to file
        await communicate.save(audio_file)
        
        print(f"Playing audio...")
        
        # Play the audio file directly
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # Wait for audio to finish playing
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Clean up pygame to release the file
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            
            print("✓ Audio playback completed.")
            
            # Delete the temporary audio file
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                    print("✓ Temporary file cleaned up.")
            except Exception as e:
                print(f"Warning: Could not delete temp file: {e}")
                
        except ImportError:
            print("Note: pygame not installed. Install with: pip install pygame")
            print(f"Audio file saved as: {audio_file}")
        
    except ImportError:
        print("Error: edge_tts not installed. Install with: pip install edge-tts")
    except Exception as e:
        print(f"Error: {e}")


async def save_to_audio_file(text, filename, voice="en-US-AriaNeural", rate=1.0):
    """
    Convert text to audio and save it to a file.
    
    Args:
        text (str): The text to convert to audio
        filename (str): Output filename (e.g., 'output.mp3')
        voice (str): Voice identifier
        rate (float): Speech rate multiplier (0.5 to 2.0)
    """
    try:
        import edge_tts
        
        # Validate and convert rate to string format
        rate = max(0.5, min(2.0, rate))
        rate_percent = int((rate - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%"
        
        print(f"Using voice: {voice}")
        print(f"Converting text to audio and saving to: {filename}")
        
        # Create communicate object
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate_str)
        
        # Save to file
        await communicate.save(filename)
        
        print(f"✓ Audio successfully saved to: {filename}")
        
    except ImportError:
        print("Error: edge_tts not installed. Install with: pip install edge-tts")
    except Exception as e:
        print(f"Error: {e}")


async def list_available_voices():
    """Display all available neural voices."""
    try:
        import edge_tts
        
        voices = await edge_tts.list_voices()
        
        print("\nAvailable Voices:")
        print("=" * 60)
        
        # Group voices by language
        voice_dict = {}
        for voice in voices:
            lang = voice["Locale"]
            name = voice["Name"]
            gender = voice["Gender"]
            
            if lang not in voice_dict:
                voice_dict[lang] = []
            voice_dict[lang].append((name, gender))
        
        for lang in sorted(voice_dict.keys()):
            print(f"\n{lang}:")
            for name, gender in voice_dict[lang]:
                print(f"  • {name:<30} ({gender})")
        
    except ImportError:
        print("Error: edge_tts not installed. Install with: pip install edge-tts")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Main function to handle command-line interface."""
    print("=" * 60)
    print("Modern Text-to-Audio Converter (Neural Voices)")
    print("=" * 60)
    print("\n✓ Auto-detects Bulgarian and English")
    print("✓ Supported voices: bg-BG-BorislavNeural, bg-BG-KalinaNeural, en-US-AriaNeural")
    print("\nOptions:")
    print("  1. Speak text now (auto-detects language)")
    print("  2. Save text as audio file")
    print("  3. List available voices")
    print("  4. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                text = input("\nEnter the text to speak: ").strip()
                if text:
                    voice = input("Enter voice (press Enter for auto-detect, or specify like en-US-AriaNeural or bg-BG-BorislavNeural): ").strip()
                    voice = voice if voice else None  # None triggers auto-detection
                    
                    rate_input = input("Enter speech rate (0.5-2.0, default 1.0): ").strip()
                    try:
                        rate = float(rate_input) if rate_input else 1.0
                    except ValueError:
                        rate = 1.0
                    
                    await text_to_audio_and_play(text, voice=voice, rate=rate)
                else:
                    print("No text provided.")
                    
            elif choice == "2":
                text = input("\nEnter the text to convert: ").strip()
                if text:
                    filename = input("Enter output filename (e.g., output.mp3): ").strip()
                    if filename:
                        voice = input("Enter voice (default en-US-AriaNeural): ").strip()
                        voice = voice if voice else "en-US-AriaNeural"
                        
                        rate_input = input("Enter speech rate (0.5-2.0, default 1.0): ").strip()
                        try:
                            rate = float(rate_input) if rate_input else 1.0
                        except ValueError:
                            rate = 1.0
                        
                        await save_to_audio_file(text, filename, voice=voice, rate=rate)
                    else:
                        print("No filename provided.")
                else:
                    print("No text provided.")
                    
            elif choice == "3":
                await list_available_voices()
                    
            elif choice == "4":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
        
        print()


async def cli_mode(text, filename=None, voice="en-US-AriaNeural", rate=1.0):
    """Handle command-line arguments."""
    if filename:
        await save_to_audio_file(text, filename, voice=voice, rate=rate)
    else:
        await text_to_audio_and_play(text, voice=voice, rate=rate)


if __name__ == "__main__":
    # If text is provided as command-line argument, process it
    if len(sys.argv) > 1:
        text_input = " ".join(sys.argv[1:])
        asyncio.run(text_to_audio_and_play(text_input))
    else:
        # Otherwise, start the interactive menu
        asyncio.run(main())
