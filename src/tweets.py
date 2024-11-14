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

    def reply_to_tweet(self, tweet_data: dict, content: str) -> None:
        """Reply to a tweet directly from notifications"""
        try:
            # Instead of navigating to the URL, find the tweet in notifications
            if not tweet_data.get('element'):
                print("No tweet element provided")
                return
                
            # Find and click reply button on the notification tweet
            reply_button = tweet_data['element'].find_element(By.CSS_SELECTOR, "[data-testid='reply']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", reply_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", reply_button)
            time.sleep(3)  # Increased wait time after clicking reply
            
            try:
                # More specific selector for the exact DraftEditor content area
                editor = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "div.notranslate.public-DraftEditor-content[data-testid='tweetTextarea_0'][contenteditable='true'][aria-label='Post text']"
                )
                
                # Click to focus the editor
                self.driver.execute_script("arguments[0].click();", editor)
                time.sleep(1)
                
                # Clear any existing text using keyboard shortcuts
                editor.send_keys('\ue009' + 'a')  # Ctrl+A
                editor.send_keys('\ue003')  # Backspace
                time.sleep(0.5)
                
                # Send content
                editor.send_keys(content)
                time.sleep(1)
                
                # Click post button
                post_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='tweetButton']")
                self.driver.execute_script("arguments[0].click();", post_button)
                time.sleep(2)
                
                print(f"Successfully replied to tweet {tweet_data['tweet_id']}")
                
            except Exception as e:
                print(f"Error entering text: {e}")
                # Fallback attempt
                try:
                    # Alternative selector focusing on the wrapping div
                    editor_wrapper = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "div[aria-label='Post text'][role='textbox'].notranslate"
                    )
                    editor_wrapper.click()
                    time.sleep(1)
                    
                    # Clear text and enter content
                    editor_wrapper.send_keys('\ue009' + 'a')  # Ctrl+A
                    editor_wrapper.send_keys('\ue003')  # Backspace
                    time.sleep(0.5)
                    editor_wrapper.send_keys(content)
                    time.sleep(1)
                    
                    post_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='tweetButton']")
                    self.driver.execute_script("arguments[0].click();", post_button)
                    time.sleep(2)
                except Exception as backup_error:
                    print(f"Backup method also failed: {backup_error}")
                    raise
            
        except Exception as e:
            print(f"Error replying to tweet: {e}")
            # Try to return to notifications page
            self.driver.get("https://twitter.com/notifications/mentions")
            time.sleep(2)

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
            # Removed the clearing of processed tweets
            # We want to maintain the history of processed tweets
            
            # Go to notifications page
            self.driver.get("https://twitter.com/notifications/mentions")
            time.sleep(5)
            
            username = os.getenv("TWITTER_USERNAME", "agent47ai").lower()
            print(f"Checking mentions for @{username}")
            
            notifications = []
            
            # Find all articles
            articles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
            print(f"Found {len(articles)} articles")
            
            for position, article in enumerate(articles, 1):
                try:
                    # Get tweet URL and ID
                    timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
                    url = timestamp.get_attribute("href")
                    tweet_id = url.split("/status/")[1]
                    
                    # Skip if we've already processed this tweet
                    if tweet_id in self.processed_tweets:
                        print(f"Skipping already processed tweet {tweet_id}")
                        continue
                    
                    # Get tweet text
                    tweet_text = article.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text
                    print(f"Processing tweet {tweet_id} at position {position}: {tweet_text[:50]}...")
                    
                    # Check if this is a mention
                    if f"@{username}" in tweet_text.lower():
                        notifications.append({
                            "text": tweet_text,
                            "tweet_id": tweet_id,
                            "url": url,
                            "element": article  # Store the article element
                        })
                        print(f"Added mention from position {position}")
                
                except Exception as e:
                    print(f"Error processing article at position {position}: {e}")
                    continue
                
                # Scroll to make next items visible
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", article)
                    time.sleep(0.5)
                except:
                    pass

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
