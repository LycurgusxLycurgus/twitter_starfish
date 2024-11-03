# src/auth.py

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
from .utils import save_cookies, load_cookies, get_env_variable
import os

class Authenticator:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.username = get_env_variable("TWITTER_USERNAME")
        self.password = get_env_variable("TWITTER_PASSWORD")
        self.email = get_env_variable("TWITTER_EMAIL")
        self.session_file = "twitter_session.json"

    def login(self):
        self.driver.get("https://twitter.com/login")
        time.sleep(3)  # Wait for page to load

        username_field = self.driver.find_element(By.NAME, "text")
        username_field.send_keys(self.username)
        username_field.send_keys(Keys.RETURN)
        time.sleep(2)

        password_field = self.driver.find_element(By.NAME, "password")
        password_field.send_keys(self.password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)  # Wait for login to complete

        # Verify login success
        try:
            self.driver.find_element(By.XPATH, "//div[@aria-label='Post text']")
            print("Login successful!")
            # Save session after successful login
            self.save_session()
            return True
        except NoSuchElementException:
            print("Login failed!")
            return False

    def save_session(self):
        """Save the current session cookies"""
        cookies = self.driver.get_cookies()
        save_cookies(cookies, self.session_file)
        print("Session saved successfully!")

    def load_session(self) -> bool:
        """Load and verify a saved session"""
        cookies = load_cookies(self.session_file)
        if not cookies:
            print("No saved session found.")
            return False

        try:
            # Load the base URL first
            self.driver.get("https://twitter.com")
            
            # Add the saved cookies
            for cookie in cookies:
                if isinstance(cookie.get('expiry', None), float):
                    cookie['expiry'] = int(cookie['expiry'])
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Warning: Could not add cookie: {e}")

            # Refresh and verify login status
            self.driver.get("https://twitter.com/home")
            time.sleep(3)
            
            # Verify we're logged in by looking for the post box
            self.driver.find_element(By.XPATH, "//div[@aria-label='Post text']")
            print("Session restored successfully!")
            return True

        except NoSuchElementException:
            print("Saved session is invalid or expired.")
            # Delete the invalid session file
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            return False
        except Exception as e:
            print(f"Error loading session: {e}")
            return False

    def logout(self):
        self.driver.get("https://twitter.com/logout")
        time.sleep(2)
        confirm_button = self.driver.find_element(By.XPATH, "//div[@data-testid='confirmationSheetConfirm']")
        confirm_button.click()
        time.sleep(3)
