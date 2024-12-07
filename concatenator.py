import os
import argparse
import random
import sys  

from pydub import AudioSegment, effects

def remove_trailing_silence(sound, silence_threshold=-50.0, chunk_size=10):
    """
    Removes trailing silence from an AudioSegment.

    Parameters:
    - sound: The AudioSegment instance to process.
    - silence_threshold: The dBFS level below which sound is considered silent (default: -50.0 dBFS).
    - chunk_size: The size of the chunks to analyze in milliseconds (default: 10 ms).

    Returns:
    - A new AudioSegment with the trailing silence removed.
    """
    end_trim = len(sound)  # Initialize the end trim point to the length of the audio

    while end_trim > 0:
        start = max(0, end_trim - chunk_size)
        chunk = sound[start:end_trim]
        
        # Check if the chunk is silent
        if chunk.dBFS < silence_threshold or chunk.dBFS == float('-inf'):
            end_trim -= chunk_size  # Move the end trim point backward
        else:
            break  # Exit the loop when a non-silent chunk is found

    # Trim the sound to the new length
    trimmed_sound = sound[:end_trim]
    return trimmed_sound

def combine_words_and_definitions(words_folder, definitions_folder, output_file, startIndex, endIndex, repeatCount, wordPause, definitionPause, normalize): 
    combined_audio = AudioSegment.empty()

    word_files = [f for f in os.listdir(words_folder) if f.endswith('.mp3')]
    definition_files = [f for f in os.listdir(definitions_folder) if f.endswith('.mp3')]

     # Sort alphabetically so that indexes map consistently to words/definitions
    word_files.sort()
    definition_files.sort()

    # compression settings:
    _threshold = -20
    _ratio = 3
    _attack = 10
    _release = 75

    # Create a list of indexes within the specified range
    indexes = list(range(startIndex, endIndex))
    last_index_played = None

    for repeat in range(repeatCount):
        print(f"Repeat {repeat + 1} of {repeatCount}")

        # Shuffle indexes to get a new study order each time
        random.shuffle(indexes)

        # If possible, avoid starting a new round with the same word as the last one played previously
        if last_index_played is not None and len(indexes) > 1:
            if indexes[0] == last_index_played:
                indexes[0], indexes[1] = indexes[1], indexes[0] 
            
        for idx in indexes:
            word_file = os.path.join(words_folder, word_files[idx])
            definition_file = os.path.join(definitions_folder, definition_files[idx])

            try:
                # Load the word audio and remove trailing silence
                word_audio = AudioSegment.from_mp3(word_file)
                word_audio = remove_trailing_silence(word_audio)

                if normalize:
                    word_audio = effects.normalize(word_audio)
                    word_audio = effects.compress_dynamic_range(
                        word_audio,
                        threshold = _threshold,
                        ratio = _ratio,
                        attack = _attack,
                        release = _release
                    )
                    word_audio = effects.normalize(word_audio)

                combined_audio += word_audio

                # Add pause after word
                combined_audio += AudioSegment.silent(duration=wordPause)

                # Load the definition audio and remove trailing silence
                definition_audio = AudioSegment.from_mp3(definition_file)
                definition_audio = remove_trailing_silence(definition_audio)

                if normalize:
                    definition_audio = effects.normalize(definition_audio)
                    definition_audio = effects.compress_dynamic_range(
                        definition_audio,
                        threshold = _threshold,
                        ratio = _ratio,
                        attack = _attack,
                        release = _release
                    )
                    definition_audio = effects.normalize(definition_audio)

                combined_audio += definition_audio

                # Add pause after definition
                combined_audio += AudioSegment.silent(duration=definitionPause)

                print(f"Added word and definition for index {idx}")
                last_index_played = idx
                
            except Exception as e:
                print(f"Error processing index {idx}: {e}")
                sys.exit(1)

    # Export the combined audio as an MP3 file
    combined_audio.export(output_file, format="mp3")
    print(f"Combined audio file created: {output_file}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Audio Flashcard Concatenator')
    parser.add_argument('--start_index', type=int, required=True,
        help='Starting index for the word/definition range')
    parser.add_argument('--end_index', type=int, required=True,
        help='Ending index for the word/definition range (inclusive)')
    parser.add_argument('--repeat_count', type=int, required=True,
        help='How many times to shuffle and repeat the flashcards')
    parser.add_argument('--word_folder', type=str, default='words',
        help='Directory containing word audio files (default "words")')
    parser.add_argument('--definition_folder', type=str, default='definitions',
        help='Directory containing definition audio files (default "definitions")')
    parser.add_argument('--output_folder', type=str, default='output',
        help='Directory to store results (default: "output")')
    parser.add_argument('--pause_after_word', type=int, default=3000,
        help='Milliseconds of silence after word before the definition (default 3000)')
    parser.add_argument('--pause_after_definition', type=int, default=1000,
        help='Milliseconds of silence after definition before next word (default 1000)')
    parser.add_argument('--normalize', action='store_true',
      help='Normalize and compress all audio clips to the same volume (default False)')
    opt = parser.parse_args()

    # Validate existence of audio source folders. 
    if not (os.path.exists(opt.word_folder) and os.path.isdir(opt.word_folder)):
        print(f"error: word folder '{opt.word_folder}' not found")
        sys.exit(1)
    if not (os.path.exists(opt.definition_folder) and os.path.isdir(opt.definition_folder)):
        print(f"error: definition folder '{opt.definition_folder}' not found")
        sys.exit(1)

    # Count available word and definition files
    word_files = [f for f in os.listdir(opt.word_folder) if f.endswith('.mp3')]
    definition_files = [f for f in os.listdir(opt.definition_folder) if f.endswith('.mp3')]
    wordCount = len(word_files)
    definitionCount = len(definition_files)

    # Validate index range
    if(opt.start_index < 0 or opt.start_index >= opt.end_index ):
        print(f"error: start_index {opt.start_index} must be >=0 and < end_index {opt.end_index}")
        sys.exit(1)
    if opt.end_index > wordCount:
        print(f"error: end_index {opt.end_index} exceeds available word count {wordCount}")
        sys.exit(1)

    if opt.end_index > definitionCount:
        print(f"error: end_index {opt.end_index} exceeds available definition count {definitionCount}")
        sys.exit(1)

    # Pause arguments must be non-negative
    if opt.pause_after_word < 0:
        print(f"error: pause_after_word cannot be negative")
        sys.exit(1)
    if opt.pause_after_definition < 0:
        print(f"error: pause_after_definition cannot be negative")
        sys.exit(1)

    # Ensure output directory exists
    if not os.path.exists(opt.output_folder):
        os.makedirs(opt.output_folder)

    # Execute the combination process
    output_file = "cards_" + str(opt.start_index) + "-" + str(opt.end_index) + ".mp3"
    output_file = os.path.join(opt.output_folder, output_file)
    combine_words_and_definitions(
        os.path.abspath(opt.word_folder), 
        os.path.abspath(opt.definition_folder), 
        output_file, 
        opt.start_index, 
        opt.end_index, 
        opt.repeat_count, 
        opt.pause_after_word, 
        opt.pause_after_definition,
        opt.normalize
    )
