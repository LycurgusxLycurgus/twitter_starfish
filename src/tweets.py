# src/tweets.py

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
import time
from typing import List
import os

class TweetManager:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.processed_tweets = set()  # Store processed tweet IDs
        self.load_processed_tweets()  # Load from persistent storage

    def load_processed_tweets(self):
        """Load processed tweet IDs from file"""
        try:
            if os.path.exists('processed_tweets.txt'):
                with open('processed_tweets.txt', 'r') as f:
                    self.processed_tweets = set(f.read().splitlines())
        except Exception as e:
            print(f"Error loading processed tweets: {e}")

    def save_processed_tweets(self):
        """Save processed tweet IDs to file"""
        try:
            with open('processed_tweets.txt', 'w') as f:
                f.write('\n'.join(self.processed_tweets))
        except Exception as e:
            print(f"Error saving processed tweets: {e}")

    def has_already_replied(self, article) -> bool:
        """Check if we've already replied to this tweet by looking at actual replies"""
        try:
            username = os.getenv("TWITTER_USERNAME", "agent47ai").lower()
            
            # Click on the article to expand replies
            try:
                # Find and click the timestamp to open the tweet
                timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
                self.driver.execute_script("arguments[0].click();", timestamp)
                time.sleep(2)
                
                # Look for replies
                replies = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                
                # Check each reply for our username
                for reply in replies:
                    try:
                        author_element = reply.find_element(By.CSS_SELECTOR, "[data-testid='User-Name']")
                        if f"@{username}" in author_element.text.lower():
                            print(f"Found existing reply from {username}")
                            return True
                    except:
                        continue
                        
                # Go back to notifications
                self.driver.get("https://twitter.com/notifications/mentions")
                time.sleep(2)
                return False
                
            except Exception as e:
                print(f"Error checking replies in article: {e}")
                return False
                
        except Exception as e:
            print(f"Error in has_already_replied: {e}")
            return False

    def clear_text_box(self) -> None:
        try:
            # Find the text box
            tweet_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Post text']")
            # Clear it using keyboard shortcuts (Ctrl+A then Backspace)
            tweet_box.send_keys('\ue009' + 'a')  # Ctrl+A
            tweet_box.send_keys('\ue003')  # Backspace
            time.sleep(0.5)  # Small wait to ensure clearing is complete
        except:
            pass  # If there's no text or element not found, just continue

    def send_tweet(self, content: str) -> None:
        """Send a new tweet with better error handling and navigation"""
        try:
            # First ensure we're on home page
            print("Navigating to home page for tweeting...")
            self.driver.get("https://twitter.com/home")
            time.sleep(3)  # Wait for page load
            
            # Try multiple selectors for the tweet box
            selectors = [
                ("xpath", "//div[@aria-label='Post text']"),
                ("xpath", "//div[@aria-label='Tweet text']"),
                ("css", "div[aria-label='Post text']"),
                ("css", "div[data-testid='tweetTextarea_0']"),
                ("css", "div[role='textbox'][aria-label='Post text']")
            ]
            
            tweet_box = None
            for method, selector in selectors:
                try:
                    if method == "xpath":
                        tweet_box = self.driver.find_element(By.XPATH, selector)
                    else:
                        tweet_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if tweet_box:
                        break
                except:
                    continue
            
            if not tweet_box:
                raise Exception("Could not find tweet input box with any selector")
            
            # Click and clear the input box
            self.driver.execute_script("arguments[0].click();", tweet_box)
            time.sleep(1)
            self.clear_text_box()
            
            # Send the content
            tweet_box.send_keys(content)
            time.sleep(1)
            
            # Try multiple selectors for the post button
            button_selectors = [
                ("css", "[data-testid='tweetButton']"),
                ("css", "div[role='button'][data-testid='tweetButtonInline']"),
                ("css", "div.css-175oi2r.r-kemksi.r-jumn1c.r-xd6kpl.r-gtdqiz.r-ipm5af.r-184en5c > div:nth-child(2) > div > div > div > button")
            ]
            
            post_button = None
            for method, selector in button_selectors:
                try:
                    post_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if post_button:
                        break
                except:
                    continue
            
            if not post_button:
                raise Exception("Could not find post button")
            
            # Click the post button
            self.driver.execute_script("arguments[0].click();", post_button)
            time.sleep(2)  # Wait for post to be sent
            
        except Exception as e:
            print(f"Error in send_tweet: {e}")
            raise  # Re-raise the exception to be handled by the main loop

    def sanitize_text(self, text: str) -> str:
        """Sanitize text to only include BMP characters"""
        return ''.join(char for char in text if ord(char) < 0xFFFF)

    def reply_to_tweet(self, tweet_data: dict, content: str) -> None:
        """Reply to a tweet directly from notifications"""
        max_retries = 3
        success = False
        
        try:
            # Sanitize the content before using it
            sanitized_content = self.sanitize_text(content)
            print(f"Sanitized content: {sanitized_content}")
            
            for attempt in range(max_retries):
                try:
                    # Find all articles again to get fresh elements
                    articles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                    target_article = None
                    
                    # Find the specific article containing our tweet ID
                    for article in articles:
                        try:
                            timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
                            url = timestamp.get_attribute("href")
                            if tweet_data['tweet_id'] in url:
                                target_article = article
                                break
                        except:
                            continue
                    
                    if not target_article:
                        raise Exception("Could not find target tweet")
                    
                    # Find and click reply button within this specific article
                    reply_button = target_article.find_element(
                        By.CSS_SELECTOR, 
                        "[data-testid='reply']"
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", reply_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", reply_button)
                    time.sleep(2)
                    
                    # Try multiple selectors for the reply box
                    selectors = [
                        "div[data-testid='tweetTextarea_0']",
                        "div[aria-label='Post text']",
                        "div.public-DraftStyleDefault-block.public-DraftStyleDefault-ltr"
                    ]
                    
                    editor = None
                    for selector in selectors:
                        try:
                            editor = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if editor:
                                break
                        except:
                            continue
                    
                    if not editor:
                        raise Exception("Could not find reply text box")
                    
                    self.driver.execute_script("arguments[0].click();", editor)
                    time.sleep(1)
                    
                    # Clear any existing text
                    editor.send_keys('\ue009' + 'a')  # Ctrl+A
                    editor.send_keys('\ue003')  # Backspace
                    time.sleep(1)
                    
                    # Enter sanitized reply content
                    editor.send_keys(sanitized_content)
                    time.sleep(1)
                    
                    # Click reply button
                    post_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='tweetButton']")
                    self.driver.execute_script("arguments[0].click();", post_button)
                    time.sleep(3)
                    
                    success = True
                    print(f"Successfully replied to tweet {tweet_data['tweet_id']}")
                    break
                    
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        # Refresh mentions page for next attempt
                        self.driver.get("https://twitter.com/notifications/mentions")
                        time.sleep(3)
                    continue
            
            if success:
                # Only save to processed tweets if reply was successful
                self.processed_tweets.add(tweet_data['tweet_id'])
                self.save_processed_tweets()
                
        except Exception as e:
            print(f"Error replying to tweet: {e}")
        finally:
            # Always return to mentions page
            print("Returning to mentions page...")
            self.driver.get("https://twitter.com/notifications/mentions")
            time.sleep(3)

    def fetch_tweets(self, username: str, count: int = 10) -> List[str]:
        self.driver.get(f"https://twitter.com/{username}")
        time.sleep(3)
        tweets = []
        tweet_elements = self.driver.find_elements(By.XPATH, "//article//div[@lang]")
        for tweet in tweet_elements[:count]:
            tweets.append(tweet.text)
        return tweets

    def extract_tweet_id(self, article) -> str:
        """Extract tweet ID from article element"""
        try:
            # Get the timestamp link which contains the tweet ID
            timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
            url = timestamp.get_attribute("href")
            return url.split("/status/")[1]
        except Exception as e:
            print(f"Error extracting tweet ID: {e}")
            return None

    def check_notifications(self) -> List[dict]:
        """Check notifications for mentions and collect tweets to reply to"""
        try:
            # Go to notifications page
            self.driver.get("https://twitter.com/notifications/mentions")
            time.sleep(5)
            
            username = os.getenv("TWITTER_USERNAME", "agent47ai").lower()
            print(f"Checking mentions for @{username}")
            
            notifications = []
            processed_count = 0
            max_scroll_attempts = 5
            scroll_attempt = 0
            
            while scroll_attempt < max_scroll_attempts:
                articles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                print(f"Found {len(articles)} total articles, processed {processed_count} so far")
                
                if processed_count >= len(articles):
                    print("No new articles found after scrolling")
                    break
                
                for article in articles[processed_count:]:
                    try:
                        # Get the actual mention tweet's URL (not the original tweet)
                        tweet_url = None
                        tweet_id = None
                        
                        # First try to get the direct URL of this tweet
                        try:
                            timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
                            tweet_url = timestamp.get_attribute("href")
                            tweet_id = tweet_url.split("/status/")[1]
                            print(f"Found mention tweet ID: {tweet_id}")
                        except Exception as e:
                            print(f"Error getting tweet URL: {e}")
                            continue
                        
                        # Skip if already processed
                        if tweet_id in self.processed_tweets:
                            print(f"Skipping already processed tweet {tweet_id}")
                            continue
                        
                        # Get tweet text and verify it's a mention
                        try:
                            tweet_text = article.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text
                            print(f"Processing tweet {tweet_id}: {tweet_text[:50]}...")
                            
                            if f"@{username}" in tweet_text.lower():
                                notifications.append({
                                    "text": tweet_text,
                                    "tweet_id": tweet_id,
                                    "url": tweet_url,
                                    "is_mention": True
                                })
                                print(f"Added new mention: {tweet_id}")
                        except Exception as e:
                            print(f"Error getting tweet text: {e}")
                            continue
                        
                    except Exception as e:
                        print(f"Error processing article: {e}")
                        continue
                
                processed_count = len(articles)
                
                if articles:
                    try:
                        last_article = articles[-1]
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", last_article)
                        time.sleep(2)
                        scroll_attempt += 1
                    except Exception as e:
                        print(f"Error scrolling: {e}")
                        break
                else:
                    break

            print(f"Found {len(notifications)} new mentions to process")
            return notifications

        except Exception as e:
            print(f"Error checking notifications: {e}")
            return []

    def check_and_process_mentions(self, generator) -> None:
        """Check and process mentions without navigation"""
        try:
            notifications = self.check_notifications()
            
            if notifications:
                print(f"Processing {len(notifications)} mentions...")
                for notification in notifications:
                    try:
                        reply_content = generator.generate_tweet(f"reply to: {notification['text']}")
                        
                        if reply_content:
                            self.reply_to_tweet(notification, reply_content)
                            self.processed_tweets.add(notification['tweet_id'])
                            self.save_processed_tweets()  # Save after each reply
                            print(f"Replied to tweet ID: {notification['tweet_id']}")
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"Error processing notification: {e}")
                        continue
            else:
                print("No new mentions to process")
                
        except Exception as e:
            print(f"Error in check_and_process_mentions: {e}")
