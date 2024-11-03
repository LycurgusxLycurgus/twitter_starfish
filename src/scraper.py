# src/scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from typing import Optional
from .auth import Authenticator
from .tweets import TweetManager

class Scraper:
    def __init__(self, proxy: Optional[str] = None):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        if proxy and proxy.strip() and proxy.lower() != "proxy_url_if_needed":
            chrome_options.add_argument(f'--proxy-server={proxy}')
        # Uncomment the next line to run in headless mode
        # chrome_options.add_argument("--headless")
        
        try:
            # Try using the WebDriver Manager first
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        except ValueError:
            # Fallback: Use the Chrome binary directly
            chrome_options.add_argument("--log-level=3")  # Suppress logging
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.auth = Authenticator(self.driver)
        self.tweets = TweetManager(self.driver)

    def initialize(self):
        if not self.auth.load_session():
            self.auth.login()

    def send_tweet(self, content: str) -> None:
        self.tweets.send_tweet(content)

    def reply_to_tweet(self, tweet_url: str, content: str) -> None:
        self.tweets.reply_to_tweet(tweet_url, content)

    def fetch_tweets(self, username: str, count: int = 10):
        return self.tweets.fetch_tweets(username, count)

    def close(self):
        self.driver.quit()
