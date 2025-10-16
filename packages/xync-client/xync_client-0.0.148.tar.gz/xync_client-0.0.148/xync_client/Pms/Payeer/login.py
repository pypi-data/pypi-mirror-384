from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from xync_schema.models import PmAgent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time


async def login(agent: PmAgent):
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless=new")  # for Chrome >= 109
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-oopr-debug-crash-dump")
    options.add_argument("--no-crash-upload")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-low-res-tiling")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = uc.Chrome(
        options=options,
        headless=False,
        browser_executable_path="/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
    )
    wait = WebDriverWait(driver, timeout=10)
    try:
        driver.get("https://payeer.com/en/auth")
        wait.until(EC.invisibility_of_element_located((By.TAG_NAME, "lottie-player")))
        login_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "button.button_empty")))
        login_link.click()
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(agent.auth.get("email"))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(agent.auth.get("password"))
        login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login-form__login-btn.step1")))
        login_button.click()
        time.sleep(4)
        try:
            login_button.click()
        except Exception:
            pass
        time.sleep(1)
        if (v := driver.find_elements(By.CLASS_NAME, "form-input-top")) and v[0].text == "Введите проверочный код":
            code = input("Email code: ")
            actions = ActionChains(driver)
            for char in code:
                actions.send_keys(char).perform()
            step2_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login-form__login-btn.step2")))
            step2_button.click()
        agent.state = {"cookies": driver.get_cookies()}
        await agent.save()
    finally:
        driver.quit()
