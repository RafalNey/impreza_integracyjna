import streamlit as st
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt


# Funkcja do zapisywania wyborów użytkownika
def save_user_selection(selected_dates, login):
    formatted_dates = [date.strftime('%Y-%m-%d') for date in selected_dates]
    new_data = pd.DataFrame({
        'login': [login],
        'dates': [','.join(formatted_dates)]
    })

    # Sprawdzenie, czy plik już istnieje
    if os.path.exists('user_selections.csv'):
        new_data.to_csv('user_selections.csv', mode='a', header=False, index=False)
    else:
        new_data.to_csv('user_selections.csv', index=False)


# Funkcja do wczytywania wyborów użytkownika
def load_user_selection(login):
    if os.path.exists('user_selections.csv'):
        df = pd.read_csv('user_selections.csv')
        user_data = df[df['login'] == login]
        if not user_data.empty:
            dates_str = user_data['dates'].values[0]
            return [datetime.datetime.strptime(date, '%Y-%m-%d').date() for date in dates_str.split(',')]
    return []


# Wczytanie poniższych danych
st.title("Impreza integracyjna kursu Data Scientist")

# Sidebar do logowania i wyboru dni
with st.sidebar:
    st.header("Logowanie i wybór dni")

    login = st.text_input("Podaj swój login z Discorda:")

    # Zmienna sesji dla zaznaczenia poprzednich wyborów
    if 'previous_selection' not in st.session_state:
        st.session_state.previous_selection = None

    if st.button("Zaloguj"):
        if login:  # Zmiana na sprawdzenie loginu
            st.session_state['authenticated'] = True

            # Resetowanie wcześniejszych wyborów przy nowym logowaniu
            st.session_state.previous_selection = []  # Resetujemy poprzedni wybór
            st.session_state.previous_selection = load_user_selection(login)  # Wczytaj wcześniej dokonane wybory
            st.success("Zalogowano! Możesz kontynuować.")
        else:
            st.session_state['authenticated'] = False
            st.error("Proszę podać login!")

    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        # Zakres dat
        start_date = datetime.date(2024, 11, 1)
        end_date = datetime.date(2024, 12, 15)

        # Generowanie dni piątków i sobót w danym zakresie
        available_days = pd.date_range(start_date, end_date)
        available_days = [date for date in available_days if date.weekday() in [4, 5]]  # 4 = piątek, 5 = sobota

        # Umożliwienie wyboru dni spotkania
        selected_dates = st.multiselect(
            "Wybierz dni spotkań (Piątki i Soboty):",
            options=available_days,
            default=[],  # Upewniamy się, że nowe wybory są puste
            format_func=lambda x: f"{x.strftime('%Y-%m-%d')} ({'pt' if x.weekday() == 4 else 'sb'})"
        )

        if st.button("Zapisz wybór"):
            save_user_selection(selected_dates, login)
            st.success("Twój wybór został zapisany!")

# Wykres na głównym ekranie
st.header("")

if os.path.exists('user_selections.csv'):
    selections_df = pd.read_csv('user_selections.csv')

    # Przekształcamy kolumnę z datami w formacie tekstowym na listę dat
    selections_df['dates'] = selections_df['dates'].apply(lambda x: x.split(',') if isinstance(x, str) else [])

    # Usunąć puste rekordy
    selections_df = selections_df[selections_df['dates'].astype(bool)]

    # Rozbijamy daty na jedną kolumnę
    selections_count = selections_df.explode('dates').groupby('dates').size().reset_index(name='count')

    # Konwersja dat na datetime
    selections_count['dates'] = pd.to_datetime(selections_count['dates'], format='%Y-%m-%d', errors='coerce')

    # Usuwamy nieprawidłowe daty
    selections_count = selections_count[selections_count['dates'].notna()]

    # Przypisanie kolorów dla piątków i sobót
    selections_count['color'] = selections_count['dates'].apply(lambda x: 'yellow' if x.weekday() == 4 else 'green')

    # Stworzenie wykresu
    fig, ax = plt.subplots(figsize=(10, 5))

    # Rysowanie słupków z kolorami
    bar = ax.bar(selections_count['dates'].dt.strftime('%Y-%m-%d'), selections_count['count'], color=selections_count['color'])

    plt.title('Liczba chętnych w wybrane dni')
    plt.xlabel('Data')
    plt.ylabel('Liczba użytkowników')
    plt.xticks(rotation=90)

    # Wyświetlenie wykresu
    st.pyplot(fig)

st.sidebar.header("Informacje")
st.sidebar.write("Proszę podać swój login z Discorda i wybrać dni, które Ci odpowiadają.")
