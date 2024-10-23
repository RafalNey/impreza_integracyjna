import streamlit as st
import pandas as pd
import datetime
import requests
import matplotlib.pyplot as plt

# Wprowadź swój klucz API
API_KEY = "AIzaSyBXPrN5wOlA_dNJWVHf320jDuogcZLVEhk"
SPREADSHEET_ID = "17sPxX_NoRy7dg5qqw_EAKgYXktcuVtW7-COHZjT6rc8"  # ID Twojego arkusza


# Funkcja do zapisywania wyborów użytkownika
def save_user_selection(selected_dates, login):
    formatted_dates = [date.strftime('%Y-%m-%d') for date in selected_dates]
    data = {
        "values": [[login, ','.join(formatted_dates)]]
    }
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Sheet1!A1:append?valueInputOption=USER_ENTERED&key={API_KEY}"

    response = requests.post(url, json=data)

    if response.status_code == 200:
        st.success("Twój wybór został zapisany!")
    else:
        st.error("Wystąpił problem podczas zapisywania wyboru.")


# Funkcja do wczytywania wyborów użytkownika
def load_user_selection(login):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Sheet1?key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        rows = data.get("values", [])
        for row in rows:
            if row[0] == login:  # Zakładamy, że login jest w pierwszej kolumnie
                dates_str = row[1]  # A daty w drugiej
                return [datetime.datetime.strptime(date, '%Y-%m-%d').date() for date in dates_str.split(',')]
    return []


# Twoja pozostała logika aplikacji
st.title("Impreza integracyjna kursu Data Scientist")

# Sidebar do logowania i wyboru dni
with st.sidebar:
    st.header("Logowanie i wybór dni:")

    login = st.text_input("Podaj swój login z Discorda:")

    if st.button("Zaloguj"):
        if login:
            st.session_state['authenticated'] = True
            st.session_state.previous_selection = load_user_selection(login)
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

url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Sheet1?key={API_KEY}"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    rows = data.get("values", [])

    df = pd.DataFrame(rows[1:], columns=rows[0])  # Zakładamy, że pierwszy wiersz to nagłówki

    # Przekształcamy kolumnę z datami w formacie tekstowym na listę dat
    df['dates'] = df['dates'].apply(lambda x: x.split(',') if isinstance(x, str) else [])

    # Usunąć puste rekordy
    df = df[df['dates'].astype(bool)]

    # Rozbijamy daty na jedną kolumnę
    selections_count = df.explode('dates').groupby('dates').size().reset_index(name='count')

    # Konwersja dat na datetime
    selections_count['dates'] = pd.to_datetime(selections_count['dates'], format='%Y-%m-%d', errors='coerce')

    # Usuwamy nieprawidłowe daty
    selections_count = selections_count[selections_count['dates'].notna()]

    # Przypisanie kolorów dla piątków i sobót
    selections_count['color'] = selections_count['dates'].apply(lambda x: 'yellow' if x.weekday() == 4 else 'green')

    # Stworzenie wykresu
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(selections_count['dates'].dt.strftime('%Y-%m-%d'), selections_count['count'], color=selections_count['color'])

    plt.title('Liczba chętnych w wybrane dni')
    plt.xlabel('Data')
    plt.ylabel('Liczba użytkowników')
    plt.xticks(rotation=90)

    # Wyświetlenie wykresu
    st.pyplot(fig)

st.sidebar.header("Informacje")
st.sidebar.write("Proszę podać swój login z Discorda i wybrać dni, które Ci odpowiadają.")
