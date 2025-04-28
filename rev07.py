import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import requests
import json
import pandas as pd
import threading
import time
import logging
import urllib3
from tkinter.scrolledtext import ScrolledText

# Sertifika uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# **Global değişkenler**
jeton = None  # Jeton değişkenini global olarak tanımla

# Tkinter log penceresi
root = tk.Tk()
root.title("Designed by KK")

log_text = ScrolledText(root, height=20, width=80, state="disabled")
log_text.pack(padx=10, pady=10, fill="both", expand=True)


# Log mesajlarını Tkinter içine yazdıran fonksiyon
def log_to_tkinter(message):
    log_text.config(state="normal")
    log_text.insert(tk.END, message + "\n")
    log_text.yview(tk.END)
    log_text.update_idletasks()
    log_text.config(state="disabled")


# Logging yapılandırması
class TkinterLogHandler(logging.Handler):
    def emit(self, record):
        log_to_tkinter(self.format(record))


logging.getLogger().addHandler(TkinterLogHandler())
logging.getLogger().setLevel(logging.INFO)

# Kullanıcı bilgileri
kullanici_adi = "kemal.kucukakkas"
sifre = "Bp*123321"
servis_anahtari = "9a8039b0-2c77-4232-9999-483dca9265c6"

# **Merkez ve Analog Ölçüm ID bilgileri**
centers = {
    '2873': {'name': 'Türkmenbeyi',
             'analog_ids': {'42873': 'aktif güç bes', '45163': 'enerji bes', '44018': 'reaktif', '58041': 'reaktif ges', '58040': 'aktif güç ges', '58042': 'enerji ges'}},
    '2655': {'name': 'Beyaz Piramit', 'analog_ids': {'42922': 'aktif güç (MW) BES', '45212': 'enerji (MWh) BES',
                                                     '44067': 'reaktif güç (MVAr) BES'}}
}

# **Tkinter giriş alanları**
center_var = tk.StringVar()
analog_id_var = tk.StringVar()
entry_ic_ihtiyac = tk.Entry(root)

# **Arayüz elemanları**
ttk.Label(root, text="Merkez Seçin:").pack()
center_dropdown = ttk.Combobox(root, textvariable=center_var, state="readonly")
center_dropdown.pack()

ttk.Label(root, text="Analog ID Seçin:").pack()
analog_id_dropdown = ttk.Combobox(root, textvariable=analog_id_var, state="readonly")
analog_id_dropdown.pack()

ttk.Label(root, text="İç İhtiyaç (kWh):").pack()
entry_ic_ihtiyac.pack()

# **Merkez listesini doldur**
center_dropdown["values"] = [f"{k} - {v['name']}" for k, v in centers.items()]


# **Analog ID'leri güncelleyen fonksiyon**
def update_analog_ids(event=None):
    selected_center = center_var.get().split()[0]
    if selected_center in centers:
        analog_id_dropdown["values"] = [f"{k} - {v}" for k, v in centers[selected_center]["analog_ids"].items()]
    else:
        analog_id_dropdown["values"] = []
    analog_id_dropdown.set("")  # Seçili değeri temizle


# **Merkez değiştiğinde analog ID'leri güncelle**
center_dropdown.bind("<<ComboboxSelected>>", update_analog_ids)

# **Başlangıçta merkezleri ve analog id'leri yükle**
if centers:
    center_var.set(next(iter(centers)))  # İlk merkezi seç
    update_analog_ids()


def login():
    global jeton  # Jeton değişkenini global olarak kullan
    login_url = "https://ytbsws.teias.gov.tr/ytbs-webservis/rest/yetkilendirme/login"
    login_payload = {"kullaniciAdi": kullanici_adi, "sifre": sifre}
    headers = {'Content-Type': 'application/json', 'SERVICE_KEY': servis_anahtari}

    try:
        response = requests.post(login_url, json=login_payload, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            jeton = response.json().get("jeton")
            logging.info(f"Jeton alındı: {jeton}")
            return True
        else:
            logging.error(f"Giriş başarısız: {response.text}")
            return False
    except requests.exceptions.RequestException:
        logging.exception("Giriş sırasında hata oluştu")
        return False


def send_data(row, center_id, analog_id, ic_ihtiyac_kwh):
    if pd.isna(row['Tarih']) or pd.isna(row['Saat']) or pd.isna(row['veriDeger']):
        logging.error("❌ Eksik veri tespit edildi, gönderim iptal edildi.")
        return False

    tarih = row['Tarih']
    saat = row['Saat']
    veriDeger = (row['veriDeger'] + ic_ihtiyac_kwh) / 1000  # kWh to MWh dönüşüm

    ekle_url = "https://ytbsws.teias.gov.tr/ytbs-webservis/rest/veritoplama/saatlikolcum/ekle"
    ekle_payload = {
        "merkezId": center_id,
        "merkezTuru": 0,
        "veri": [{
            "tarih": tarih,
            "saat": saat,
            "analogOlcumId": analog_id,
            "veriDeger": veriDeger
        }]
    }
    headers = {'Content-Type': 'application/json', 'SERVICE_KEY': servis_anahtari, 'AUTH_TOKEN': jeton}

    logging.info(f"Gönderiliyor: Tarih={tarih}, Saat={saat}, AnalogID={analog_id}, VeriDeger={veriDeger}")

    try:
        response = requests.post(ekle_url, json=ekle_payload, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            logging.info("✅ Veri başarıyla gönderildi!")
            return True
        else:
            logging.error(f"❌ Veri gönderme başarısız: {response.text}")
            return False
    except requests.exceptions.RequestException:
        logging.exception("🔴 Veri ekleme sırasında ağ hatası oluştu")
        return False

def delete_today_data():
    global jeton

    if jeton is None and not login():
        return

    center_id = center_var.get().split()[0]
    merkez_turu = 0  # Santral

    today = time.strftime("%Y-%m-%d")
    sil_url = "https://ytbsws.teias.gov.tr/ytbs-webservis/rest/veritoplama/saatlikolcum/sil"
    sil_payload = {
        "merkezId": center_id,
        "merkezTuru": merkez_turu,
        "tarih": today
    }
    headers = {
        'Content-Type': 'application/json',
        'SERVICE_KEY': servis_anahtari,
        'AUTH_TOKEN': jeton
    }

    logging.info(f"🧹 Bugünün verisi siliniyor: Merkez={center_id}, Tarih={today}")

    try:
        response = requests.post(sil_url, json=sil_payload, headers=headers, timeout=10, verify=False)
        if response.status_code == 200 and response.json().get("basarili"):
            logging.info("✅ Bugüne ait veriler başarıyla silindi!")
        else:
            logging.error(f"❌ Silme işlemi başarısız: {response.text}")
    except requests.exceptions.RequestException:
        logging.exception("🔴 Silme sırasında ağ hatası oluştu")


def login_and_send_data():
    global jeton  # Jeton değişkenini global olarak kullan

    if jeton is None and not login():
        return

    file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
    if not file_path:
        logging.error("📁 Dosya seçilmedi!")
        return

    try:
        df = pd.read_excel(file_path)

        # **Sütun isimlerini yazdır ve kontrol et**
        logging.info(f"📊 Excel Sütunları: {list(df.columns)}")

        if 'Tarih Saat' in df.columns:
            df['Tarih Saat'] = pd.to_datetime(df['Tarih Saat'], errors='coerce')  # Tarihe çevir
            if df['Tarih Saat'].isna().all():
                logging.error("❌ 'Tarih Saat' sütunu tamamen geçersiz! Lütfen tarihi kontrol edin.")
                return
            df['Tarih'] = df['Tarih Saat'].dt.strftime('%Y-%m-%d')
            df['Saat'] = df['Tarih Saat'].dt.strftime('%H:%M')
        else:
            logging.error("❌ Excel dosyasında 'Tarih Saat' sütunu bulunamadı!")
            return

        df['veriDeger'] = pd.to_numeric(df.iloc[:, 1], errors='coerce')

    except Exception as e:
        logging.exception("❌ Excel verisi işlenirken hata oluştu")
        return

    center_id = center_var.get().split()[0]
    analog_id = analog_id_var.get().split()[0]
    ic_ihtiyac_kwh = float(entry_ic_ihtiyac.get())

    for _, row in df.iterrows():
        send_data(row, center_id, analog_id, ic_ihtiyac_kwh)
        time.sleep(0.1)


# **Buton ekle**
ttk.Button(root, text="Verileri Gönder", command=login_and_send_data).pack()
ttk.Button(root, text="Bugünün Verilerini Sil", command=delete_today_data).pack()


root.mainloop()
