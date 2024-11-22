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

    def clean_content(self, content: str) -> str:
        """Clean tweet content of metadata and partial content"""
        # Remove editing notes in parentheses
        content = content.split("**(")[0].strip()
        
        # If there are multiple attempts at content (indicated by the same starting words)
        # take only the first complete one
        lines = content.split('\n')
        if len(lines) > 1:
            return lines[0].strip()
        
        return content.strip()

    def sanitize_text(self, text: str) -> str:
        """Sanitize text to only include BMP characters"""
        # First clean the content
        text = self.clean_content(text)
        # Then remove non-BMP characters
        return ''.join(char for char in text if ord(char) < 0xFFFF)

    def reply_to_tweet(self, tweet_data: dict, content: str) -> None:
        """Reply to a tweet directly from notifications or search"""
        max_retries = 3
        success = False
        
        try:
            # Clean and sanitize the content
            content = self.sanitize_text(content)
            print(f"Replying with content: {content}")
            
            for attempt in range(max_retries):
                try:
                    # Return to appropriate page for fresh elements
                    if tweet_data.get('is_fwog'):
                        self.driver.get("https://x.com/search?q=%24fwog&src=typeahead_click")
                    else:
                        self.driver.get("https://twitter.com/notifications")
                    time.sleep(3)
                    
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
                    
                    # Rest of the reply logic remains the same...
                    reply_button = target_article.find_element(By.CSS_SELECTOR, "[data-testid='reply']")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", reply_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", reply_button)
                    time.sleep(2)
                    
                    # Find and interact with reply box
                    editor = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']")
                    self.driver.execute_script("arguments[0].click();", editor)
                    time.sleep(1)
                    
                    # Clear any existing text
                    editor.send_keys('\ue009' + 'a')  # Ctrl+A
                    editor.send_keys('\ue003')  # Backspace
                    time.sleep(1)
                    
                    # Enter reply content
                    editor.send_keys(content)
                    time.sleep(1)
                    
                    # Click reply button
                    post_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='tweetButton']")
                    self.driver.execute_script("arguments[0].click();", post_button)
                    time.sleep(3)
                    
                    success = True
                    break
                    
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise
                
            if success:
                self.processed_tweets.add(tweet_data['tweet_id'])
                self.save_processed_tweets()
                
        except Exception as e:
            print(f"Error replying to tweet: {e}")
        finally:
            # Return to appropriate page
            if tweet_data.get('is_fwog'):
                self.driver.get("https://x.com/search?q=%24fwog&src=typeahead_click")
            else:
                self.driver.get("https://twitter.com/notifications")
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
            # Go to main notifications page instead of mentions
            self.driver.get("https://twitter.com/notifications")
            time.sleep(5)
            
            username = os.getenv("TWITTER_USERNAME", "agent47ai").lower()
            print(f"Checking notifications for @{username}")
            
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
                        # Get tweet URL and ID
                        timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
                        url = timestamp.get_attribute("href")
                        tweet_id = url.split("/status/")[1]
                        print(f"Found tweet ID: {tweet_id}")
                        
                        # Skip if already processed
                        if tweet_id in self.processed_tweets:
                            print(f"Skipping already processed tweet {tweet_id}")
                            continue
                        
                        # Get tweet text
                        tweet_text = article.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text
                        print(f"Processing tweet {tweet_id}: {tweet_text[:50]}...")
                        
                        # Check if this is a mention
                        if f"@{username}" in tweet_text.lower():
                            notifications.append({
                                "text": tweet_text,
                                "tweet_id": tweet_id,
                                "url": url,
                                "element": article  # Store the article element
                            })
                            print(f"Added mention from position {processed_count + 1}")
                    
                    except Exception as e:
                        print(f"Error processing article: {e}")
                        continue
                
                processed_count = len(articles)
                
                # Scroll to make next items visible
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
        """Check and process both mentions and $fwog tweets"""
        try:
            # First process notifications (existing functionality)
            print("\n=== Checking Notifications ===")
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
            
            # Then process $fwog tweets
            print("\n=== Checking $fwog Tweets ===")
            fwog_tweets = self.check_fwog_tweets()
            
            if fwog_tweets:
                print(f"Processing {len(fwog_tweets)} $fwog tweets...")
                for tweet in fwog_tweets:
                    try:
                        reply_content = generator.generate_tweet(f"reply to $fwog tweet: {tweet['text']}")
                        
                        if reply_content:
                            self.reply_to_tweet(tweet, reply_content)
                            self.processed_tweets.add(tweet['tweet_id'])
                            self.save_processed_tweets()
                            print(f"Replied to $fwog tweet ID: {tweet['tweet_id']}")
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"Error processing $fwog tweet: {e}")
                        continue
            else:
                print("No new $fwog tweets to process")
            
            # Return to home page
            print("\nReturning to home page...")
            self.driver.get("https://twitter.com/home")
            time.sleep(3)
                
        except Exception as e:
            print(f"Error in check_and_process_mentions: {e}")
            self.driver.get("https://twitter.com/home")
            time.sleep(3)

    def check_fwog_tweets(self) -> List[dict]:
        """Check tweets containing $fwog and collect them for replies"""
        try:
            # Go to $fwog search page with correct URL
            search_url = "https://x.com/search?q=%24fwog&src=typeahead_click"
            print(f"\nNavigating to $fwog search: {search_url}")
            self.driver.get(search_url)
            time.sleep(5)  # Wait for search page to load
            
            print("Checking $fwog tweets...")
            
            fwog_tweets = []
            processed_count = 0
            max_scroll_attempts = 15  # Increased from 5 to 15
            scroll_attempt = 0
            last_height = 0
            
            while scroll_attempt < max_scroll_attempts:
                # Get current scroll height
                current_height = self.driver.execute_script("return document.documentElement.scrollHeight")
                
                articles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                print(f"Found {len(articles)} total $fwog tweets, processed {processed_count} so far")
                
                if processed_count >= len(articles) and current_height == last_height:
                    print("No new $fwog tweets found after scrolling")
                    break
                
                for article in articles[processed_count:]:
                    try:
                        # Get tweet URL and ID
                        timestamp = article.find_element(By.CSS_SELECTOR, "time").find_element(By.XPATH, "./..")
                        url = timestamp.get_attribute("href")
                        tweet_id = url.split("/status/")[1]
                        print(f"Found $fwog tweet ID: {tweet_id}")
                        
                        # Skip if already processed
                        if tweet_id in self.processed_tweets:
                            print(f"Skipping already processed $fwog tweet {tweet_id}")
                            continue
                        
                        # Get tweet text
                        tweet_text = article.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text
                        print(f"Processing $fwog tweet {tweet_id}: {tweet_text[:50]}...")
                        
                        # Find reply button to verify we can interact with it
                        reply_button = article.find_element(By.CSS_SELECTOR, "[data-testid='reply']")
                        
                        # Only add tweets that actually contain $fwog and have a reply button
                        if "$fwog" in tweet_text.lower() and reply_button:
                            fwog_tweets.append({
                                "text": tweet_text,
                                "tweet_id": tweet_id,
                                "url": url,
                                "element": article,
                                "is_fwog": True  # Mark as fwog tweet
                            })
                            print(f"Added $fwog tweet from position {processed_count + 1}")
                        else:
                            print(f"Skipping tweet {tweet_id} - does not contain $fwog or no reply button")
                    
                    except Exception as e:
                        print(f"Error processing $fwog tweet: {e}")
                        continue
                
                processed_count = len(articles)
                
                # Scroll to make next items visible
                if articles:
                    try:
                        # Scroll to bottom
                        self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                        time.sleep(3)  # Increased wait time after scroll
                        
                        # Wait for new content
                        for _ in range(10):  # Check multiple times for new content
                            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
                            if new_height != current_height:
                                break
                            time.sleep(0.5)
                        
                        last_height = current_height
                        scroll_attempt += 1
                        
                    except Exception as e:
                        print(f"Error scrolling $fwog tweets: {e}")
                        break
                else:
                    break

            print(f"Found {len(fwog_tweets)} new $fwog tweets to process")
            return fwog_tweets

        except Exception as e:
            print(f"Error checking $fwog tweets: {e}")
            return []

    def process_notifications(self, generator) -> None:
        try:
            while True:  # Continuous monitoring loop
                # First check notifications (existing functionality)
                print("\n=== Checking Notifications ===")
                notifications = self.check_notifications()
                
                if notifications:
                    print(f"Processing {len(notifications)} notifications...")
                    for notification in notifications:
                        try:
                            reply_content = generator.generate_tweet(f"reply to: {notification['text']}")
                            
                            if reply_content:
                                self.reply_to_tweet(notification, reply_content)
                                self.processed_tweets.add(notification['tweet_id'])
                                self.save_processed_tweets()
                                print(f"Replied to notification ID: {notification['tweet_id']}")
                                time.sleep(2)
                                
                        except Exception as e:
                            print(f"Error processing notification: {e}")
                            continue
                else:
                    print("No new notifications to process")
                
                # Then check $fwog tweets
                print("\n=== Checking $fwog Tweets ===")
                fwog_tweets = self.check_fwog_tweets()
                
                if fwog_tweets:
                    print(f"Processing {len(fwog_tweets)} $fwog tweets...")
                    for tweet in fwog_tweets:
                        try:
                            reply_content = generator.generate_tweet(f"reply to $fwog tweet: {tweet['text']}")
                            
                            if reply_content:
                                self.reply_to_tweet(tweet, reply_content)
                                self.processed_tweets.add(tweet['tweet_id'])
                                self.save_processed_tweets()
                                print(f"Replied to $fwog tweet ID: {tweet['tweet_id']}")
                                time.sleep(2)
                                
                        except Exception as e:
                            print(f"Error processing $fwog tweet: {e}")
                            continue
                else:
                    print("No new $fwog tweets to process")
                
                # Return to home page and wait before next check
                print("\nReturning to home page...")
                self.driver.get("https://twitter.com/home")
                time.sleep(3)
                print("Waiting 1 minute before next check...")
                time.sleep(60)  # 1 minute interval
                
        except Exception as e:
            print(f"Error in process_notifications: {e}")
            self.driver.get("https://twitter.com/home")
            time.sleep(3)
