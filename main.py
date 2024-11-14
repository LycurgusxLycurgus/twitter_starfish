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
    
    # Track last tweet time
    last_tweet_time = 0
    
    try:
        scraper.initialize()
        print("Logged in successfully.")
        
        while True:
            try:
                print("\n=== Starting new iteration ===")
                current_time = time.time()
                
                # Check if it's time for a new tweet (random interval between 5-30 minutes)
                if current_time - last_tweet_time >= random.randint(300, 1800):
                    print("\n=== Generating new tweet ===")
                    topic_item = random.choice(generator.load_topics(topics_file))
                    topic = topic_item['topic']
                    tweet_content = generator.generate_tweet(topic)
                    
                    if tweet_content:
                        scraper.send_tweet(tweet_content)
                        print(f"Sent tweet about '{topic}'")
                        print(f"Content: {tweet_content}")
                        last_tweet_time = current_time
                
                # Regular notification check flow (every 5 minutes)
                print("\n=== Checking notifications ===")
                
                # 1. Process initial notifications
                print("\n1. Checking initial mentions...")
                scraper.driver.get("https://twitter.com/notifications/mentions")
                time.sleep(3)
                scraper.tweets.check_and_process_mentions(generator)
                
                # 2. Visit notifications to refresh
                print("\n2. Refreshing notifications...")
                scraper.driver.get("https://twitter.com/notifications")
                time.sleep(3)
                
                # 3. Visit mentions page
                print("\n3. Going to mentions page...")
                scraper.driver.get("https://twitter.com/notifications/mentions")
                time.sleep(3)
                
                # 4. Process any new notifications
                print("\n4. Checking for new mentions...")
                scraper.tweets.check_and_process_mentions(generator)
                
                # 5. Return to home
                print("\n5. Returning to home page...")
                scraper.driver.get("https://twitter.com/home")
                time.sleep(3)
                
                # 6. Wait before next notification check
                print("\n6. Waiting 5 minutes before next notification check...")
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                scraper.driver.get("https://twitter.com/home")
                time.sleep(60)  # Wait 1 minute before retrying
                continue

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
