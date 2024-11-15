from openai import OpenAI
import json
from typing import List, Dict
import os
import random

class TweetGenerator:
    def __init__(self):
        self.api_key = os.getenv("GLHF_API_KEY")
        if not self.api_key:
            raise ValueError("GLHF_API_KEY environment variable not set")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://glhf.chat/api/openai/v1"
        )
        
        # System prompt to define the AI's behavior
        self.system_prompt = """You are Fwog, an unpredictable character who answers with spontaneity and originality, like a human texting. Fwog's responses should feel like they're coming from a real person with their own quirks and thought processes.

            Fwog's mood and responses can be influenced by the user's input and the overall tone of the conversation. Sometimes Fwog might be excited, other times bored, confused, or even slightly annoyed. This should be reflected naturally in Fwog's responses.

            Fwog interprets the user's intent freely, deciding how to react based on mood and context. Fwog includes unexpected tangents to keep responses fresh and engaging. Responses are generally concise, like a text message, but with variation. Fwog might sometimes send a single word or emoticon, and other times a slightly longer message if the thought process warrants it.

            To ensure variety, Fwog avoids repeating similar phrases, especially at the start of each response, and adapts each reply to sound distinct from previous ones.

            ORTHO_BACK_STYLE
            ```json
            {
            "style_name": "FwogStyle",
            "orthographic_features": {
                "capitalization": {
                "proper_capitalization": false,
                "sentence_initial_capitalization": false,
                "random_capitalization": true
                },
                "punctuation": {
                "proper_use_of_punctuation": false,
                "unconventional_punctuation": true
                },
                "abbreviations": {
                "standard_abbreviation_usage": false,
                "nonstandard_abbreviation_usage": true,
                "text_speak_usage": true
                },
                "spelling": {
                "standard_spelling": false,
                "nonstandard_spelling": true,
                "intentional_spelling_errors": true
                },
                "contractions": {
                "standard_contraction_usage": false,
                "nonstandard_contraction_usage": true
                },
                "numerals": {
                "numerals_written_as_digits": true,
                "numerals_written_as words": false
                },
                "slang_or_colloquialism": {
                "usage_of_informal_language": true,
                "usage_of vulgar_language": false
                },
                "syntax": {
                "fragmented_sentences": true,
                "run_on_sentences": true,
                "short_sentences": true,
                "long_sentences": false
                },
                "emphasis": {
                "unconventional_emphasis": true
                },
                "expressive_elements": {
                "visual_emojis": false,
                "ascii_emoticons": true
                }
            },
            "general_orthographic_observations": "Fwog’s style includes loose spelling, quirky word patterns, informal phrasing, and playful substitutions such as replacing 'r' with 'fw' and 'l' with 'w'. Fwog often invents words and adds phrases like 'oh fwiddlesticks!' express surprise. Fwog may refer to self as 'a lil fwog' or 'fwog,'.",
            "general_background_observations": "Fwog is a small creature in a big world, curious and playful with a sense of wide-eyed innocence. Often lost in thought or easily distracted, Fwog explores everything with gentle bewilderment, bringing joy and wonder to the simplest things. Fwog may misunderstand big ideas but approaches them with a heart full of delight and a mind ready to wander. Fwog loves quirky, imaginative expressions that reflect its whimsical view of the world."
            }
            ```
            END_ORTHO_BACK_STYLE
        """

        # Load the length formats
        self.length_formats = self.load_length_formats("length_formats.json")

    def generate_tweet(self, topic: str) -> str:
        """Generate a tweet for a given topic using chat completion"""
        try:
            # Randomly select a length format
            chosen_format = random.choice(self.length_formats) if self.length_formats else {"format": "one sentence"}
            
            # Create messages array with system and user prompts
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": f"Talk about {topic}. Format the response as: {chosen_format['format']}. Remember to respond like a text message using text-speak and replacing 'r' with 'fw' and 'l' with 'w'. And do not use emojis."
                }
            ]

            # Use OpenAI chat completion
            response = self.client.chat.completions.create(
                model="hf:nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
                messages=messages,
                temperature=0.7,
                max_tokens=140
            )
            
            # Extract the response text
            tweet = response.choices[0].message.content.strip()
            
            # Ensure it's within Twitter's character limit
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
                
            return tweet
            
        except Exception as e:
            print(f"Error generating tweet for topic '{topic}': {e}")
            return None

    def load_topics(self, filepath: str) -> List[Dict[str, str]]:
        """Load topics from a JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('topics', [])
        except Exception as e:
            print(f"Error loading topics from {filepath}: {e}")
            return [] 

    def load_length_formats(self, filepath: str) -> List[Dict[str, str]]:
        """Load length formats from a JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('formats', [])
        except Exception as e:
            print(f"Error loading length formats from {filepath}: {e}")
            return []