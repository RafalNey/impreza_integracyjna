import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from streamlit_gsheets import GSheetsConnection

# Tworzenie obiektu połączenia z GSheets
conn = st.connection("gsheets", type=GSheetsConnection, token="your_gsheets_token.json")
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/17sPxX_NoRy7dg5qqw_EAKgYXktcuVtW7-COHZjT6rc8/edit?usp=sharing'


def load_data():
    # Wczytanie wszystkich danych z arkusza
    df = conn.read(spreadsheet_url)
    return df


def save_user_selection(selected_dates, login):
    data = {
        "dates": ','.join([date.strftime('%Y-%m-%d') for date in selected_dates]),
        "login": login
    }

    conn.write(data)  # Zakładamy, że istnieje metoda do zapisu


# Logika aplikacji
st.title("Impreza integracyjna kursu Data Scientist")

# Sidebar do logowania i wyboru dni
with st.sidebar:
    st.header("Logowanie i wybór dni:")
    login = st.text_input("Podaj swój login z Discorda:")

    if st.button("Zaloguj"):
        if login:
            st.session_state['authenticated'] = True
            st.session_state.previous_selection = load_data()
            st.success("Zalogowano! Możesz kontynuować.")
        else:
            st.session_state['authenticated'] = False
            st.error("Proszę podać login!")

    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        start_date = datetime.date(2024, 11, 1)
        end_date = datetime.date(2024, 12, 15)
        available_days = pd.date_range(start_date, end_date)
        available_days = [date for date in available_days if date.weekday() in [4, 5]]

        selected_dates = st.multiselect(
            "Wybierz dni spotkań (Piątki i Soboty):",
            options=available_days,
            default=[],
            format_func=lambda x: f"{x.strftime('%Y-%m-%d')} ({'pt' if x.weekday() == 4 else 'sb'})"
        )

        if st.button("Zapisz wybór"):
            save_user_selection(selected_dates, login)

# Wykres na głównym ekranie
st.header("Liczba chętnych w wybrane dni")

df = load_data()

# Przekształć dane i stwórz wykres
df['dates'] = df['dates'].apply(lambda x: x.split(',') if isinstance(x, str) else [])
df = df[df['dates'].astype(bool)]
selections_count = df.explode('dates').groupby('dates').size().reset_index(name='count')
selections_count['dates'] = pd.to_datetime(selections_count['dates'], format='%Y-%m-%d', errors='coerce')
selections_count = selections_count[selections_count['dates'].notna()]
selections_count['color'] = selections_count['dates'].apply(lambda x: 'yellow' if x.weekday() == 4 else 'green')

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(selections_count['dates'].dt.strftime('%Y-%m-%d'), selections_count['count'], color=selections_count['color'])

plt.title('Liczba chętnych w wybrane dni')
plt.xlabel('Data')
plt.ylabel('Liczba użytkowników')
plt.xticks(rotation=90)

st.pyplot(fig)

st.sidebar.header("Informacje")
st.sidebar.write("Proszę podać swój login z Discorda i wybrać dni, które Ci odpowiadają.")
