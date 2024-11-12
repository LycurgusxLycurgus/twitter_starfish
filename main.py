# main.py

import os
from src import Scraper
from src.ai_generator import TweetGenerator
from dotenv import load_dotenv
import time
from datetime import datetime
import random

def main():
    load_dotenv()  # Load environment variables from .env file

    proxy = os.getenv("PROXY_URL")  # Optional: Set proxy if needed
    topics_file = os.getenv("TOPICS_FILE", "topics.json")  # Path to topics JSON file
    
    scraper = Scraper(proxy=proxy)
    generator = TweetGenerator()
    
    try:
        scraper.initialize()
        print("Logged in successfully.")
        
        while True:
            try:
                # Check notifications and reply to mentions
                scraper.tweets.process_notifications(generator)
                print("Processed notifications")
                
                # Generate and send periodic tweet
                topic_item = random.choice(generator.load_topics(topics_file))
                topic = topic_item['topic']
                tweet_content = generator.generate_tweet(topic)
                
                if tweet_content:
                    scraper.send_tweet(tweet_content)
                    print(f"Sent tweet about '{topic}'")
                    print(f"Content: {tweet_content}\n")
                
                # Wait before next iteration
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
                continue

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
