import streamlit as st
import sqlite3
import hashlib

# ==== 1. Veritabanı bağlantısı ve tablo oluşturma ====

def create_connection():
    conn = sqlite3.connect('biogaz.db')
    return conn

def create_user_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password, role):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_pw, role))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('SELECT role FROM users WHERE username=? AND password=?', (username, hashed_pw))
    data = cursor.fetchone()
    conn.close()
    return data

def get_all_users():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def delete_user(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username=?', (username,))
    conn.commit()
    conn.close()

# ==== 2. Başlangıç Setup (ilk çalıştırmada sadece bir kere lazım) ====

def setup_default_users():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    if count == 0:
        add_user("admin", "admin1234", "admin")
        add_user("operator1", "op1234", "operator")
        add_user("operator2", "op5678", "operator")

# ==== 3. Ana Giriş Fonksiyonu ====

def login_page():
    st.title("🔒 Kullanıcı Girişi")

    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        role = authenticate_user(username, password)
        if role:
            st.success(f"Giriş başarılı: {username}")
            st.session_state["login"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role[0]
            st.experimental_rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")

# ==== 4. Admin Paneli ====

def admin_panel():
    st.title("👤 Kullanıcı Yönetimi (Admin Paneli)")

    st.subheader("Mevcut Kullanıcılar")
    users = get_all_users()
    for user, role in users:
        st.write(f"**{user}** ({role})")

    st.subheader("Yeni Kullanıcı Ekle")
    with st.form("new_user"):
        new_username = st.text_input("Yeni Kullanıcı Adı")
        new_password = st.text_input("Yeni Şifre", type="password")
        new_role = st.selectbox("Yetki", ["admin", "operator"])
        submitted = st.form_submit_button("Ekle")
        if submitted:
            if new_username and new_password:
                add_user(new_username, new_password, new_role)
                st.success(f"{new_username} kullanıcısı eklendi!")
                st.experimental_rerun()
            else:
                st.error("Boş alan bırakmayın!")

    st.subheader("Kullanıcı Sil")
    user_to_delete = st.selectbox("Silinecek Kullanıcı", [u[0] for u in users if u[0] != "admin"])
    if st.button("Kullanıcıyı Sil"):
        delete_user(user_to_delete)
        st.success(f"{user_to_delete} silindi!")
        st.experimental_rerun()

# ==== 5. Operator Sayfası (Veri Girişi Yeri) ====

def operator_page():
    st.title("📄 Günlük Veri Girişi Sayfası")
    st.info("Buraya günlük hammadde, fermentör besleme ve laboratuvar verileri giriş ekranlarını ekleyeceğiz.")

# ==== 6. Uygulama Akışı ====

def main():
    create_user_table()
    setup_default_users()

    if "login" not in st.session_state:
        st.session_state["login"] = False

    if not st.session_state["login"]:
        login_page()
    else:
        st.sidebar.write(f"👤 Giriş Yapan: {st.session_state['username']} ({st.session_state['role']})")
        if st.sidebar.button("Çıkış Yap"):
            st.session_state.clear()
            st.experimental_rerun()

        if st.session_state["role"] == "admin":
            admin_panel()
        elif st.session_state["role"] == "operator":
            operator_page()
        else:
            st.error("Geçersiz yetki tanımı!")

if __name__ == "__main__":
    main()
