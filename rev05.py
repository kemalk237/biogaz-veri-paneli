from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By  # Bu satır önemli!
from webdriver_manager.chrome import ChromeDriverManager
import time


options = Options()
options.add_argument("--start-maximized")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://web.whatsapp.com")
print("QR kodu okutarak giriş yapın...")
time.sleep(20)  # Manuel olarak QR kod okutma süresi

# Belirli bir grubun veya kişinin adı
hedef_grup = "BP Teknik"
grup = driver.find_element(By.XPATH, f'//span[@title="{hedef_grup}"]')
grup.click()

# Son mesajları al
time.sleep(5)
mesajlar = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")

for mesaj in mesajlar[-10:]:  # son 10 mesaj
    try:
        icerik = mesaj.find_element(By.CSS_SELECTOR, "span.selectable-text").text
        print("Mesaj:", icerik)
    except:
        print("Medya veya boş mesaj.")
