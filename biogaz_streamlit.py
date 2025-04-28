import streamlit as st

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Beyaz Piramit Biyogaz Santrali",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Başlık
st.markdown(
    "<h1 style='text-align: center; color: #228B22;'>Biyogaz Veri Paneli 🌱</h1>",
    unsafe_allow_html=True
)

st.write("")
st.success("Streamlit altyapısı başarıyla hazır! Artık geliştirmeye başlayabiliriz.")

# Sidebar (Yan Menü)
with st.sidebar:
    st.header("Menü")
    menu_selection = st.radio("Git:", ["Günlük Veri Girişi", "Laboratuvar Girişi", "Raporlar"])

# Ana Ekran Bilgilendirme
st.info(f"Seçili Menü: **{menu_selection}**")
