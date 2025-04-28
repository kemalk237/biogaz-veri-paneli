import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import warnings

# Uyarıları bastır
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.styles.stylesheet")

# Saatlik üretimi hesaplayan fonksiyon
def hesapla_uretim(excel_yolu, sayac_carpani):
    df = pd.read_excel(excel_yolu)

    df["Aktif Endeks Veriş"] = (df["Aktif Endeks Veriş"].astype(str)
                                  .str.replace('.', '', regex=False)
                                  .str.replace(',', '.', regex=False)
                                  .astype(float))

    df["Profil Tarihi"] = pd.to_datetime(df["Profil Tarihi"], dayfirst=True)
    df = df.set_index("Profil Tarihi").resample("h").first()
    df["Endeks Farkı"] = df["Aktif Endeks Veriş"].diff()
    df["Saatlik Üretim (kWh)"] = df["Endeks Farkı"] * sayac_carpani
    df["Saatlik Üretim (MWh)"] = (df["Saatlik Üretim (kWh)"] / 1000).round(3)

    df = df[["Saatlik Üretim (MWh)"]].dropna()
    df.reset_index(inplace=True)
    df["Profil Tarihi"] = df["Profil Tarihi"] - pd.Timedelta(hours=1)  # EPIAŞ uyumu için saat geri kaydır

    return df

# GUI Arayüzü
class UretimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Saatlik Üretim Hesaplayıcı")

        self.sayac_label = tk.Label(root, text="Sayaç Çarpanı:")
        self.sayac_label.pack()
        self.sayac_entry = tk.Entry(root)
        self.sayac_entry.insert(0, "4725")
        self.sayac_entry.pack(pady=5)

        self.btn_yukle = tk.Button(root, text="Excel Yükle", command=self.yukle_dosya)
        self.btn_yukle.pack(pady=10)

        self.tablo = ttk.Treeview(root)
        self.tablo.pack(expand=True, fill="both", padx=10, pady=10)

        self.df_sonuc = None

        self.btn_kaydet = tk.Button(root, text="Excel'e Kaydet", command=self.kaydet_dosya)
        self.btn_kaydet.pack(pady=5)

    def yukle_dosya(self):
        dosya_yolu = filedialog.askopenfilename(filetypes=[("Excel Dosyaları", "*.xlsx")])
        if dosya_yolu:
            try:
                sayac_carpani = float(self.sayac_entry.get())
                self.df_sonuc = hesapla_uretim(dosya_yolu, sayac_carpani)
                self.goster_tablo(self.df_sonuc)
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def goster_tablo(self, df):
        for i in self.tablo.get_children():
            self.tablo.delete(i)

        self.tablo["columns"] = list(df.columns)
        self.tablo["show"] = "headings"

        for col in df.columns:
            self.tablo.heading(col, text=col)

        for idx, row in df.iterrows():
            self.tablo.insert("", "end", values=list(row))

    def kaydet_dosya(self):
        if self.df_sonuc is not None:
            dosya_yolu = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                     filetypes=[("Excel Dosyaları", "*.xlsx")])
            if dosya_yolu:
                self.df_sonuc.to_excel(dosya_yolu, index=False)
                messagebox.showinfo("Başarılı", "Dosya kaydedildi: " + dosya_yolu)
        else:
            messagebox.showwarning("Uyarı", "Önce bir dosya yüklemelisiniz.")

# Çalıştır
if __name__ == "__main__":
    root = tk.Tk()
    app = UretimApp(root)
    root.geometry("600x450")
    root.mainloop()
