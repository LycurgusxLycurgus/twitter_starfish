# main.py

import os
from src import Scraper
from src.ai_generator import TweetGenerator
from dotenv import load_dotenv
import time
from datetime import datetime
import random

def main():
    load_dotenv()
    proxy = os.getenv("PROXY_URL")
    topics_file = os.getenv("TOPICS_FILE", "topics.json")
    
    scraper = Scraper(proxy=proxy)
    generator = TweetGenerator()
    
    try:
        scraper.initialize()
        print("Logged in successfully.")
        
        last_tweet_time = 0
        tweet_interval = random.randint(300, 1800)  # Random interval between 30-60 minutes
        notification_interval = 60  # 5 minutes
        last_notification_check = 0
        
        while True:
            try:
                current_time = time.time()
                
                # Check notifications on regular schedule
                if current_time - last_notification_check >= notification_interval:
                    print("\n=== Checking Notifications ===")
                    
                    # Process notifications (keeping existing working flow)
                    print("\n1. Checking mentions...")
                    scraper.driver.get("https://twitter.com/notifications/mentions")
                    time.sleep(3)
                    scraper.tweets.check_and_process_mentions(generator)
                    
                    # Refresh notifications
                    print("\n2. Refreshing notifications...")
                    scraper.driver.get("https://twitter.com/notifications")
                    time.sleep(3)
                    
                    print("\n3. Checking mentions again...")
                    scraper.driver.get("https://twitter.com/notifications/mentions")
                    time.sleep(3)
                    scraper.tweets.check_and_process_mentions(generator)
                    
                    last_notification_check = current_time
                    print(f"\nNext notification check in {notification_interval/60} minutes")
                
                # Generate tweets on random schedule
                if current_time - last_tweet_time >= tweet_interval:
                    print("\n=== Generating Tweet ===")
                    
                    # Navigate to home for tweeting
                    scraper.driver.get("https://twitter.com/home")
                    time.sleep(3)
                    
                    # Generate and send tweet
                    topic_item = random.choice(generator.load_topics(topics_file))
                    topic = topic_item['topic']
                    
                    # Get the chosen format before generating the tweet
                    chosen_format = random.choice(generator.length_formats)['format'] if generator.length_formats else "one sentence"
                    tweet_content = generator.generate_tweet(topic)
                    
                    if tweet_content:
                        # Sanitize the tweet before sending
                        sanitized_tweet = scraper.tweets.sanitize_text(tweet_content)
                        scraper.send_tweet(sanitized_tweet)
                        print(f"Sent tweet about '{topic}'")
                        print(f"Using format: '{chosen_format}'")
                        print(f"Content: {sanitized_tweet}")
                        
                        last_tweet_time = current_time
                        tweet_interval = random.randint(300, 1800)  # New random interval
                        print(f"\nNext tweet in {tweet_interval/60:.1f} minutes")
                
                # Short sleep to prevent CPU overuse
                time.sleep(60)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                scraper.driver.get("https://twitter.com/home")
                time.sleep(60)
                continue

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
