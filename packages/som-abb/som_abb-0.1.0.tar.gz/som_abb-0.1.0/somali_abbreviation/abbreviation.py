import json
import re
import os

# Load abbreviation dictionary
def load_abbreviation_dict():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "data", "abbreviation_dict.json")
    with open(json_path, "r") as f:
        return json.load(f)

abbreviation_dict = load_abbreviation_dict()

def replace_abbreviations(text):
    # Convert to lowercase to handle case insensitivity
    text_lower = text.lower()
    
    # Replace any sequence of 'k' longer than 2 with "Qosol"
    text_lower = re.sub(r'k{3,}', 'Qosol', text_lower)

    # Replace any sequence of 'h' longer than 2 with "Qosol"
    text_lower = re.sub(r'h{3,}', 'Qosol', text_lower)
    
    # Split the modified text into words
    words = text_lower.split()
    replaced_words = []
    
    total_abbreviations = 0
    successful_translations = 0

    for word in words:
        # Convert the word to lowercase for matching
        word_clean = word.strip(",.?!")  # Remove common punctuation for better matching
        
        # Check if the word is in the abbreviation dictionary
        if word_clean in abbreviation_dict:
            total_abbreviations += 1  # Count abbreviation
            replaced_words.append(abbreviation_dict[word_clean])
            successful_translations += 1  # Count successful translation
        else:
            replaced_words.append(word)  # If not abbreviation, keep the original word
    
    # Reconstruct the sentence
    translated_text = ' '.join(replaced_words)
    
    # Calculate the accuracy percentage
    accuracy = (successful_translations / total_abbreviations) * 100 if total_abbreviations > 0 else 0
    
    return translated_text, accuracy, total_abbreviations, successful_translations
