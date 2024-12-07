import os
import sys
import csv
import json
import argparse
import requests
from enum import Enum

from elevenlabs import save
from elevenlabs.client import ElevenLabs
from elevenlabs.client import VoiceSettings

import google.cloud.texttospeech as tts


def downloadJapanesePronunciation_forvo(APIKey, word, filename):
    """
    Downloads a pronunciation recording from Forvo for a given Japanese word.

    Parameters:
    - APIKey (str): Forvo API key.
    - word (str): The Japanese word to download the pronunciation for.
    - filename (str): The file path to save the downloaded MP3.

    Returns:
    - True if the download was successful, False otherwise.
    """

    base_url = 'https://apifree.forvo.com/key/{key}/format/json/action/word-pronunciations/word/{word}/language/{language}'

    # Construct the request URL
    url = base_url.format(key=APIKey, word=word, language='ja')

    # Make the API request
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    # Check for API errors
    if 'error' in data:
        print(f"API error: {data['error']}")
        return False

    if 'items' in data and len(data['items']) > 0:
        # Get the first pronunciation URL
        pronunciation_url = data['items'][0]['pathmp3']

        # Download the pronunciation file
        audio_response = requests.get(pronunciation_url)
        audio_response.raise_for_status()

        with open(filename, 'wb') as f:
            f.write(audio_response.content)

        print(f"Pronunciation saved to {filename}")
        return True
    else:
        print(f"No pronunciations found for '{word}' in language 'ja'")
        return False
    

def downloadEnglish_elevenLabs(APIKey, definition, fileName):
    """
    Downloads an english TTS generation from ElevenLabs

    Parameters:
    - APIKey (str): ElevenLabs API key.
    - definition (str): The English definition text to synthesize.
    - fileName (str): The file path to save the generated MP3.
    """
    # short scentences sometimes causes elevelabs voices to add gibberish.
    # Adding a period and a pause seems to increase stability.
    definition += '. <break time="2.0s" />'

    client = ElevenLabs(
        api_key=APIKey,
    )

    audio = client.generate(
        text=definition,
        voice="Brian",
        model="eleven_turbo_v2",
        voice_settings=VoiceSettings(stability=1.0, similarity_boost=0.0)
    )
    save(audio, fileName)


googleTTS_ja_male   = "ja-JP-Neural2-C"
googleTTS_ja_female = "ja-JP-Neural2-B"
googleTTS_en_male   = "en-US-Neural2-A"
googleTTS_en_female = "en-US-Neural2-C"

def downloadVoice_GoogleTTS(voice_name, text, filename):
    """
    Downloads a TTS generation from the Google Cloud Text-to-Speech API

    Parameters:
    - voice_name (str): The specific TTS voice name to use.
    - text (str): The text to synthesize into speech.
    - filename (str): The file path to save the generated MP3.
    """

    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )

    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    with open(filename, "wb") as out:
        out.write(response.audio_content)

def loadCards(cardsFile):
    cards = []
    with open(cardsFile, 'r', encoding='utf-8', errors='replace') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            card = Card(word=row['Word'], definition=row['Definition'])
            cards.append(card)
    return cards

class Card:
    def __init__(self, word, definition):
        self.word = word
        self.definition = definition

class WordVoiceSource(Enum):
    Forvo = 1
    GoogleTTS = 2
class DefinitionVoiceSource(Enum):
    ElevenLabs = 1
    GoogleTTS = 2

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Audio Flashcard Audio Sourcer')
    parser.add_argument('--card_file', type=str, default="cards.csv",
        help='File path to csv containing words and definitions (default "cards.csv")')
    parser.add_argument('--start_index', type=int, default=0,
        help='Starting row index of the CSV to source audio for (default 0)')
    parser.add_argument('--end_index', type=int, default=-1,
        help='Ending row index (exclusive) of the CSV to source audio for. -1 for all rows (default -1)')
    parser.add_argument('--API_key_file', type=str, default="API_keys.json",
        help='file containing API keys (default "API_keys.json")')
    parser.add_argument('--download_words', action='store_true',
      help='Download words found in the csv (default False)')
    parser.add_argument('--download_definitions', action='store_true',
      help='Download definitions found in the csv (default False)')
    parser.add_argument('--word_source', type=str, default="Forvo",
        help='Source for word pronunciations [Forvo, GoogleTTS] (default "Forvo")')
    parser.add_argument('--definition_source', type=str, default="ElevenLabs",
        help='Source for definition readings [ElevenLabs, GoogleTTS] (default "ElevenLabs")') 
    parser.add_argument('--word_folder', type=str, default='words',
        help='Output directory for word audio files (default "words")')
    parser.add_argument('--definition_folder', type=str, default='definitions',
        help='Output directory for definition audio files (default "definitions")')
    opt = parser.parse_args()

    if opt.download_words == False and opt.download_definitions == False:
        print(f"nothing to do. Use --download_words and/or --download_definitions")
        sys.exit(0)

      # Validate card file
    if os.path.exists(opt.card_file) == False:
        print(f"error: {opt.card_file} not found")
        sys.exit(1)

    cards = loadCards(opt.card_file)

    if(opt.end_index == -1):
        opt.end_index = len(cards)

    if(opt.start_index < 0 or opt.start_index >= opt.end_index ):
        print(f"error: start_index {opt.start_index} is out of range")
        sys.exit(1)

    if(opt.end_index <= 0 or opt.end_index > len(cards)):
        print(f"error: end_index {opt.start_index} is out of range. CSV has {len(cards)} rows.")
        sys.exit(1)

    # Determine word source
    wordSource = WordVoiceSource.Forvo
    if opt.download_words:
        if opt.word_source.lower() == "forvo":
            wordSource = WordVoiceSource.Forvo
        elif opt.word_source.lower() == "googletts":
            wordSource = WordVoiceSource.GoogleTTS
        else:
            print(f"error: unkown word source \"{opt.word_source}\". must be \"Forvo\" or \"GoogleTTS\"")
            sys.exit(1)
    else:
        wordSource = None  # Not used

    # Determine definition source
    definitionSource = DefinitionVoiceSource.ElevenLabs
    if opt.download_definitions:
        if opt.definition_source.lower() == "elevenlabs":
            definitionSource = DefinitionVoiceSource.ElevenLabs
        elif opt.definition_source.lower() == "googletts":
            definitionSource = DefinitionVoiceSource.GoogleTTS
        else:
            print(f"error: unkown word source \"{opt.definition_source}\". must be \"ElevenLabs\" or \"GoogleTTS\"")
            sys.exit(1)
    else:
        definitionSource = None  # Not used

    api_keys = None
    if not os.path.exists(opt.API_key_file):
        print(f"API key file {opt.API_key_file} not found.")
        sys.exit(1)
    with open(opt.API_key_file, 'r') as file:
        api_keys = json.load(file)

    # Authenticate Google API if needed
    if ((opt.download_words and wordSource == WordVoiceSource.GoogleTTS) or 
        (opt.download_definitions and definitionSource == DefinitionVoiceSource.GoogleTTS)):
        # Check if Google credintials are already set
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_keys["googleTTS"]

    # Ensure output directories exist
    if opt.download_words:
        os.makedirs(opt.word_folder, exist_ok=True)
    if opt.download_definitions:
        os.makedirs(opt.definition_folder, exist_ok=True)

    # Process each card in the specified index range
    for idx in range(opt.start_index, opt.end_index):
        card = cards[idx]
        padded_idx = str(idx).zfill(5)

        # Download word pronunciation if requested
        if opt.download_words:
            word_file_name =  f"word_{padded_idx}.mp3"  
            word_file_path = os.path.join(opt.word_folder, word_file_name)        

            print(f"Downloading word audio for '{card.word}' to '{word_file_name}'")

            if wordSource == WordVoiceSource.Forvo:
                try:
                     # Attempt to download from Forvo
                    found = downloadJapanesePronunciation_forvo(api_keys["Forvo"], card.word, word_file_path)
                    if not found:
                        # Have not implemented a solution for this scenario yet.
                        print(f"Error: No pronunciation found for '{card.word}'. Consider removing this row from the CSV.")
                        sys.exit(1)     
                except Exception as e:
                    print(f"error downloading word audio for '{card.word}' at index {idx}: {e}")
                    sys.exit(1)

            elif wordSource == WordVoiceSource.GoogleTTS:
                try:
                    downloadVoice_GoogleTTS(googleTTS_ja_female, card.word, word_file_path)
                except Exception as e:
                    print(f"error downloading word audio for '{card.word}' at index {idx}: {e}")
                    sys.exit(1)
                    
        # Download definition audio if requested
        if opt.download_definitions:

            definition_file_name = f"definition_{padded_idx}.mp3"
            definition_file_path = os.path.join(opt.definition_folder, definition_file_name)

            print(f"Downloading definition audio for '{card.word}' to '{definition_file_name}'")

            if definitionSource == DefinitionVoiceSource.ElevenLabs:
                downloadAttempts = 4
                while True:
                    try:
                        # Make multiple attempts at this in case of "heavy traffic"
                        downloadEnglish_elevenLabs(api_keys["ElevenLabs"], card.definition, definition_file_path)
                        break
                    except Exception as e:
                        downloadAttempts -= 1
                        if downloadAttempts <= 0:
                            print(f"error downloading definition audio for '{card.word}' at index {idx}: {e}")
                            sys.exit(1)
            elif definitionSource == DefinitionVoiceSource.GoogleTTS:
                try:
                    downloadVoice_GoogleTTS(googleTTS_en_male, card.definition, definition_file_path)
                except Exception as e:
                    print(f"error downloading definition audio for '{card.word}' at index {idx}: {e}")
                    sys.exit(1)

    print(f"Audio sourcing complete! downloaded aduio for {(opt.end_index - opt.start_index)} rows")