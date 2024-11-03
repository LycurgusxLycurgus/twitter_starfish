# main.py

import os
from src import Scraper
from src.ai_generator import TweetGenerator
from dotenv import load_dotenv
import time
from datetime import datetime
import random

def send_periodic_tweets(scraper: Scraper, generator: TweetGenerator, topics_file: str, interval_minutes: int = 5):
    """Send AI-generated tweets periodically at specified interval"""
    try:
        tweet_counter = 1
        topics = generator.load_topics(topics_file)
        
        if not topics:
            raise ValueError("No topics found in the topics file")

        while True:
            # Select a random topic
            topic_item = random.choice(topics)
            topic = topic_item['topic']
            
            # Generate tweet content
            tweet_content = generator.generate_tweet(topic)
            if tweet_content:
                # Send the tweet
                scraper.send_tweet(tweet_content)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Tweet #{tweet_counter} about '{topic}' sent successfully at {current_time}")
                print(f"Content: {tweet_content}\n")
                
                tweet_counter += 1
                time.sleep(interval_minutes * 60)  # Convert minutes to seconds
            else:
                print(f"Skipping tweet generation due to error, trying again in 1 minute...")
                time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nTweet automation stopped by user.")
    except Exception as e:
        print(f"An error occurred during tweet automation: {e}")

def main():
    load_dotenv()  # Load environment variables from .env file

    proxy = os.getenv("PROXY_URL")  # Optional: Set proxy if needed
    topics_file = os.getenv("TOPICS_FILE", "topics.json")  # Path to topics JSON file
    
    scraper = Scraper(proxy=proxy)
    generator = TweetGenerator()
    
    try:
        scraper.initialize()
        print("Logged in successfully.")
        
        # Start periodic tweets
        print(f"Starting automated AI-generated tweets every 5 minutes. Press Ctrl+C to stop.")
        print(f"Using topics from: {topics_file}")
        send_periodic_tweets(scraper, generator, topics_file)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
