package main

import (
	"encoding/base64"
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/atselvan/ankiconnect"
	"github.com/privatesquare/bkst-go-utils/utils/errors"
)

func must[T any](v T, err *errors.RestErr) T {
	if err != nil {
		if err.StatusCode == 500 {
			fmt.Println("REST error: Make sure Anki is running with Anki-connect enabled.")
		}
		fmt.Printf("REST error details: %v\n", err)
		panic(err)
	}
	return v
}

type card struct {
	word       string
	definition string
}

var (
	cardQuery       = flag.String("card_query", "", "Anki search query for data to download (e.g., 'deck:MyDeck')")
	wordField       = flag.String("word_field", "", "Field name where words are stored on cards")
	definitionField = flag.String("definition_field", "", "Field name where word definitions are stored on cards")
	scrapeAudio     = flag.Bool("get_audio", false, "Download word pronunciation audio files from cards")
	wordAudioField  = flag.String("word_audio_field", "", "Field name where word pronunciation audio files are stored on cards")
	wordFolder      = flag.String("word_folder", "words_anki", "Directory to store downloaded word audio files")
	csvName         = flag.String("csv_name", "cards.csv", "Output CSV file name for word/definition pairs")
)

func main() {

	flag.Parse()

	// Validate required flags
	if *cardQuery == "" {
		fmt.Println("error: must supply --card_query")
		os.Exit(1)
	}
	if *wordField == "" {
		fmt.Println("error: must supply --word_field")
		os.Exit(1)
	}
	if *definitionField == "" {
		fmt.Println("error: must supply --definition_field")
		os.Exit(1)
	}

	// If audio scraping is requested, validate related fields and ensure directory exists.
	if *scrapeAudio {
		if *wordAudioField == "" {
			fmt.Println("error: must supply --word_audio_field when --get_audio is enabled")
			os.Exit(1)
		}
		if *wordFolder == "" {
			fmt.Println("error: must supply valid --word_folder when --get_audio is enabled")
			os.Exit(1)
		}

		if _, err := os.Stat(*wordFolder); os.IsNotExist(err) {
			err = os.Mkdir(*wordFolder, 0755)
			if err != nil {
				fmt.Printf("error: failed to create directory %s: %v\n", *wordFolder, err)
				os.Exit(1)
			}
		}
	}

	// Connect to Anki
	client := ankiconnect.NewClient()

	// Retrieve cards based on the provided query
	cardsRes := must(client.Cards.Get(*cardQuery))

	if len(*cardsRes) == 0 {
		fmt.Println("error: query returned no cards")
		os.Exit(1)
	}

	cards := make([]card, len(*cardsRes))

	for i, c := range *cardsRes {

		// Validate that the required fields exist in the card
		_, found := c.Fields[*wordField]
		if !found{
			fmt.Printf("error: card does not contain field %s\n", *wordField)
			os.Exit(1)
		}
		_, found = c.Fields[*definitionField]
		if !found{
			fmt.Printf("error: card does not contain field %s\n", *definitionField)
			os.Exit(1)
		}

		cards[i].word = c.Fields[*wordField].Value
		cards[i].definition = c.Fields[*definitionField].Value

		if *scrapeAudio {

			_, found = c.Fields[*wordAudioField]
			if !found{
				fmt.Printf("error: card does not contain field %s\n", *definitionField)
				os.Exit(1)
			}

			// Retrieve the audio file from Anki
			filename := strings.TrimSuffix(strings.TrimPrefix(c.Fields[*wordAudioField].Value, "[sound:"), "]")
			audioData := must(client.Media.RetrieveMediaFile(filename))
			decodedData, decErr := base64.StdEncoding.DecodeString(*audioData)
			if decErr != nil {
				fmt.Printf("error: failed to decode audio data for %s: %v\n", filename, decErr)
				os.Exit(1)
			}

			// Write audio file to disk
			outname := fmt.Sprintf("word_%04d.mp3", i)
			outname = filepath.Join(*wordFolder, outname)
			err := os.WriteFile(outname, decodedData, 0644)
			if err != nil {
				fmt.Printf("error: failed to write audio file %s: %v\n", outname, err)
				os.Exit(1)
			}	
			fmt.Printf("downloaded %s\n", filename)
		}
	}

	// Create CSV file
	file, err := os.Create(*csvName)
	if err != nil {
		fmt.Printf("error: failed to create CSV file %s: %v\n", *csvName, err)
		os.Exit(1)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write CSV header
	header := []string{"Word", "Definition"}
	err = writer.Write(header)
	if err != nil {
		fmt.Printf("error: failed to write CSV header: %v\n", err)
		os.Exit(1)
	}

	// Write card data
	for _, c := range cards {
		record := []string{c.word, c.definition}
		err = writer.Write(record)
		if err != nil {
			fmt.Printf("error: failed to write record for word '%s': %v\n", c.word, err)
			os.Exit(1)
		}
	}

	fmt.Printf("Successfully wrote %d cards to %s\n", len(cards), *csvName)
	os.Exit(0)
}
