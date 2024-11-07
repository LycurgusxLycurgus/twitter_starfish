# src/tweets.py

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
import time
from typing import List

class TweetManager:
    def __init__(self, driver: WebDriver):
        self.driver = driver

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
        # Find and click the "What is happening?!" input area
        tweet_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Post text']")
        tweet_box.click()
        # Clear any existing text first
        self.clear_text_box()
        tweet_box.send_keys(content)
        time.sleep(1)  # Wait for button to become enabled
        
        # Use more specific CSS selector that targets the button element
        css_selector = "div.css-175oi2r.r-kemksi.r-jumn1c.r-xd6kpl.r-gtdqiz.r-ipm5af.r-184en5c > div:nth-child(2) > div > div > div > button"
        post_button = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        post_button.click()
        time.sleep(2)  # Wait for post to be sent

    def reply_to_tweet(self, tweet_url: str, content: str) -> None:
        self.driver.get(tweet_url)
        time.sleep(3)
        reply_button = self.driver.find_element(By.XPATH, "//div[@data-testid='reply']")
        reply_button.click()
        time.sleep(2)
        reply_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Post text']")
        reply_box.send_keys(content)
        # Use the same button selector for consistency
        css_selector = "div.css-175oi2r.r-kemksi.r-jumn1c.r-xd6kpl.r-gtdqiz.r-ipm5af.r-184en5c > div:nth-child(2) > div > div > div > button"
        post_button = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        post_button.click()
        time.sleep(2)  # Wait for reply to be posted

    def fetch_tweets(self, username: str, count: int = 10) -> List[str]:
        self.driver.get(f"https://twitter.com/{username}")
        time.sleep(3)
        tweets = []
        tweet_elements = self.driver.find_elements(By.XPATH, "//article//div[@lang]")
        for tweet in tweet_elements[:count]:
            tweets.append(tweet.text)
        return tweets
