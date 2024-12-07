# Commuter Flashcards

**Study Japanese language flashcards hands-free with audio-focused tools.**

Commuter Flashcards is designed to help you learn Japanese vocabulary efficiently while driving, commuting, or in situations where traditional flashcard methods aren't practical. It converts your Anki flashcards or a CSV vocabulary list into shufflable, repeatable audio lessons.

## Features
- Extract vocabulary and definitions from Anki decks or a custom CSV file.
- Generate high-quality audio for words and their definitions using:
  - Native speaker recordings (via Forvo)
  - Text-to-speech (Google TTS, ElevenLabs)
- Create MP3 files for hands-free learning:
    - Words and definitions play in succession.
    - Randomized order to prevent memorization of patterns.
    - Efficient repetition of small word ranges to reinforce memory.

## Why Commuter Flashcards?
Traditional flashcards aren't practical in hands-free scenarios such as driving. Podcasts and other media can help language learners, but beginners may struggle to pick up new vocabulary without sufficient context.

Commuter Flashcards bridges this gap by providing recall-based listening practice. Words are read aloud, followed by their definitions, giving you a chance to recall their meaning. 

While obviously not a replacement for spaced repetition systems, this approach allows you to make productive use of downtime that would otherwise be wasted.

# Installation Instructions
1. Install Prerequisites:
    - Python
    - Golang
    - Anki-Connect (required if using anki_downloader)
2. Set up Repository:<br/>
Download repo as a ZIP or use terminal/command promp:
```sh
cd path-to-install-location/
git clone https://github.com/Michael-Manning/commuter-flashcards.git
```
3. Install dependencies and build anki_downloader
```sh
cd commuter-flashcards/
pip install -r requirements.txt
go build -o anki_downloader.exe
```

# Getting Started
## Overview of Tools
The repository includes three utilities for building audio flashcard "lessons":

**Anki Downloader:** Extracts words and definitions from Anki decks as well as audio readings of words.<br/>
**Audio Sourcer**: Downloads generated audio for words and definitions.<br/>
**Concatenator**: Combines audio clips into repeatable, shuffled lessons.<br/>

## Step 1: Creating a Card CSV
### Option 1: Manual Creation
You can create a CSV file manually with two columns:

Word: The Japanese vocabulary.<br/>
Definition: The corresponding English definition.<br/>
```text
Word, Definition
くれる,to give
入る,to enter
おはよう,good morning
```

### Option 2: Generating from Anki
Use the anki_downloader utility to export cards:

Example:
```sh
anki_downloader --card_query "deck:Refold JP1K v3" --word_field Word --definition_field Definition
```

**Arguments**
- `--card_query`: Specify the deck or search query (see exaxamples or [ankiweb docs](https://docs.ankiweb.net/searching.html#tags-decks-cards-and-notes)).
- `--word_field` / `--definition_field`: Define the card fields to extract words and definitions.
- `--get_audio`: Enable downloading of existing audio from Anki. (optional)
- `--word_audio_field`: Specify the field containing audio file names. (optional)
- `--help`: See more optional arguments.

This will generate a cards.csv file and optionally a words_anki folder containing audio clips.

## Step 2: Generating Audio Clips
Use the audio_sourcer.py utility to generate audio for vocabulary and definitions:


**Supported Audio Sources**
- Vocabulary Audio
  - Forvo (native speaker recordings)
  - Google TTS (synthetic)
- Definition Audio:
  - ElevenLabs (high-quality English TTS)
  - Google TTS (synthetic)

**API Key Configuration**
Save API keys you want to use in a API_keys.json file:
```json
{
    "Forvo": "your_forvo_api_key",
    "ElevenLabs": "your_elevenlabs_api_key",
    "googleTTS": "path_to_google_tts_service_file.json"
}
```

Example:
```sh
python audio_sourcer.py --download_words --word_source Forvo --download_definitions --definition_source ElevenLabs
```

**Arguments**
- `--start_index` / `--end_index`: Specify the row range in the card CSV (default: all rows).
- `--download_words` / `--download_definitions`: Enable audio generation.
- `--word_source` Choose the word audio provider (Forvo or GoogleTTS).
- `--definition_source` Choose the definition audio provider (ElevenLabs or GoogleTTS)
- `--help`: See more optional arguments.

This will attempt to generate and download audio for every word, definition, or both from the specified csv range and store the numbered audio clips in corresponding folders.


## Step 3: Building Lessons
Combine audio clips into lessons using concatenator.py:

Example:
```sh
python concatenator.py --start_index 0 --end_index 15 --repeat_count 5 --normalize
```
**Arguments**
- `--start_index` / `--end_index`: Specify the range of clips to include in the lesson.
- `--repeat_count`: Number of times to shuffle and repeat the range.
- `--pause_after_word` / `--pause_after_definition`: Add delays (in milliseconds) between word and definition.
- `--word_folder`: You may need to specify "words_anki" if you sourced your audio clips from your Anki deck. (optional)
- `--normalize`: Normalize and compress dynamic range to make the volume of audio consistent (optional)
- `--help`: See more optional arguments.

## Example usage

### Refold JP1K v3

Using the high quality vocab readings provided by the Refold JP1K v3 deck and GoogleTTS for english definitions.

```sh
cd commuter-flashcards
```

Generate cards.csv and word audio (make sure Anki is running):
```sh
./anki_downloader --card_query '"deck:Refold JP1K v3"' --word_field Word --definition_field  Definition --get_audio --word_audio_field word_audio
```

Source the word definition audio for the first 45 cards:
```sh
python audio_sourcer.py --download_definitions --definition_source GoogleTTS --end_index 45
```

generate multiple lessons using the audio:
```sh
python concatenator.py --start_index 0 --end_index 15 --repeat_count 5 --word_folder words_anki --normalize
python concatenator.py --start_index 15 --end_index 30 --repeat_count 5 --word_folder words_anki --normalize
python concatenator.py --start_index 30 --end_index 45 --repeat_count 5 --word_folder words_anki --normalize
python concatenator.py --start_index 0 --end_index 45 --repeat_count 3 --word_folder words_anki --normalize
```

### Tango N5

Using the high quality vocab readings provided by the Nukemarine Tango N5 deck and ElevenLabs for english definitions.

```sh
cd commuter-flashcards
```

Generate cards.csv and word audio (make sure Anki is running):
```sh
./anki_downloader --card_query '"deck:JLPT Tango" card:Listening' --word_field Tango_Vocab_Japanese --definition_field  Tango_Vocab_English --get_audio --word_audio_field Tango_Vocab_Audio
```

Source the word definition audio for the first 45 cards:
```sh
python audio_sourcer.py --download_definitions --definition_source ElevenLabs --end_index 45
```

generate multiple lessons using the audio:
```sh
python concatenator.py --start_index 0 --end_index 15 --repeat_count 5 --word_folder words_anki --normalize
python concatenator.py --start_index 15 --end_index 30 --repeat_count 5 --word_folder words_anki --normalize
python concatenator.py --start_index 30 --end_index 45 --repeat_count 5 --word_folder words_anki --normalize
python concatenator.py --start_index 0 --end_index 45 --repeat_count 3 --word_folder words_anki --normalize
```