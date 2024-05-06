from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


############################### login test ###############################

def login_and_add_stuff(username, password):
    # Setting up the Chrome WebDriver
    driver = webdriver.Chrome()

    try:

        # Navigate to the login page
        driver.get("https://irentstuff.app/login/")

        # Use WebDriverWait to ensure that the elements are loaded
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "uname"))
        )
        password_field = driver.find_element(By.NAME, "password")

        # Enter login credentials
        username_field.send_keys(username)
        password_field.send_keys(password)

        # Submit the form
        password_field.send_keys(Keys.RETURN)

        # Wait for successful login
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "identifier_of_an_element_unique_to_logged_in_users"))
        )
        print("Login successful!")


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser window
        driver.quit()

# Provide your login credentials
username = "user2"
password = "mtech@111"

# Call the function to login and add stuff
login_and_add_stuff(username, password)


############################### category search test ###############################

# def search_by_category(category):
#     # Setting up the Chrome WebDriver
#     driver = webdriver.Chrome()

#     try:
#         # Navigate to the homepage
#         driver.get("https://irentstuff.app/")

#         # Find the category dropdown menu
#         category_dropdown = driver.find_element(By.NAME, "category")

#         # Select the desired category from the dropdown menu
#         category_dropdown.send_keys(category)

#         # Find and click on the search button
#         search_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-outline-light")
#         search_button.click()

#         # Optionally, wait for the search results to load
#         WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='search-results']")))

#         print(f"Search for category '{category}' successful!")
#     except TimeoutException:
#         print("Timeout occurred while waiting for search results.")
#     except Exception as e:
#         print(f"An error occurred during search: {e}")
#     finally:
#         # Close the browser window
#         driver.quit()

# # Example usage:
# search_by_category("Bags")

############################### view item test ###############################


# def login(driver, username, password):
#     try:
#         # Navigate to the login page
#         driver.get("https://irentstuff.app/login/")

#         # Find username and password fields and submit button
#         username_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "uname")))
#         password_input = driver.find_element(By.NAME, "password")
#         login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

#         # Enter login credentials
#         username_input.send_keys(username)
#         password_input.send_keys(password)

#         # Submit the login form
#         login_button.click()

#         # Wait for the greeting message to appear after successful login
#         WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Hello, user2')]")))

#         print("Login successful!")
#         return True
#     except Exception as e:
#         print(f"An error occurred during login: {e}")
#         return False

# def perform_actions_on_stuff_page(driver, username, stuff_id):
#     # Check if login is successful
#     if not login(driver, username, "mtech@111"):
#         print("Login failed. Unable to proceed.")
#         return

#     try:
#         # Navigate to the Stuff page
#         stuff_url = f"https://irentstuff.app/stuff/{stuff_id}/"
#         driver.get(stuff_url)

#         # Wait for page elements to load
#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "stuff-page")))

#         # Example action: Click on a button with a specific class
#         add_to_cart_button = driver.find_element(By.CLASS_NAME, "add-to-cart-button")
#         add_to_cart_button.click()

#         print("Action performed successfully on Stuff page!")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# # Create a WebDriver instance
# driver = webdriver.Chrome()

# # Example usage:
# perform_actions_on_stuff_page(driver, "user2", "5")

# # Close the browser window
# driver.quit()