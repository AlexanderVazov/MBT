#!/usr/bin/env python3
"""
Text-to-Audio Script
Converts terminal input text into audio and plays it.
"""

import pyttsx3
import sys


def text_to_audio(text, rate=150, volume=0.9, voice_index=0):
    """
    Convert text to audio and play it.
    
    Args:
        text (str): The text to convert to audio
        rate (int): Speech rate (default: 150 words per minute)
        volume (float): Volume level (0.0 to 1.0)
        voice_index (int): Voice index (0 or 1 for most systems)
    """
    try:
        # Initialize the text-to-speech engine
        engine = pyttsx3.init()
        
        # Set speech rate
        engine.setProperty('rate', rate)
        
        # Set volume
        engine.setProperty('volume', volume)
        
        # Set voice (optional - use available voices)
        voices = engine.getProperty('voices')
        if voice_index < len(voices):
            engine.setProperty('voice', voices[voice_index].id)
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"Error: {e}")


def save_to_audio_file(text, filename, rate=150, volume=0.9):
    """
    Convert text to audio and save it to a file.
    
    Args:
        text (str): The text to convert to audio
        filename (str): Output filename (e.g., 'output.mp3')
        rate (int): Speech rate (default: 150 words per minute)
        volume (float): Volume level (0.0 to 1.0)
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        
        # Save to file
        engine.save_to_file(text, filename)
        engine.runAndWait()
        
        print(f"Audio saved to: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main function to handle command-line interface."""
    print("=" * 50)
    print("Text-to-Audio Converter")
    print("=" * 50)
    print("\nOptions:")
    print("  1. Speak text now")
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
                    rate = input("Enter speech rate (default 150): ").strip()
                    rate = int(rate) if rate.isdigit() else 150
                    print("\nSpeaking...")
                    text_to_audio(text, rate=rate)
                else:
                    print("No text provided.")
                    
            elif choice == "2":
                text = input("\nEnter the text to convert: ").strip()
                if text:
                    filename = input("Enter output filename (e.g., output.mp3): ").strip()
                    if filename:
                        save_to_audio_file(text, filename)
                    else:
                        print("No filename provided.")
                else:
                    print("No text provided.")
                    
            elif choice == "3":
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                print("\nAvailable voices:")
                for i, voice in enumerate(voices):
                    print(f"  {i}: {voice.name}")
                    
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


if __name__ == "__main__":
    # If text is provided as command-line argument, speak it directly
    if len(sys.argv) > 1:
        text_input = " ".join(sys.argv[1:])
        text_to_audio(text_input)
    else:
        # Otherwise, start the interactive menu
        main()
