import streamlit as st
import yaml
from yaml.loader import SafeLoader

from utils.ui import inject_css

# Streamlit page title and icon configuration
st.set_page_config(
    page_title="Interview Assistant - Nutzungsbedingungen",
)

inject_css("static/styles.css")

st.sidebar.page_link('Interview.py', label='Startseite')
st.sidebar.page_link('pages/1_Interview_Assistant.py', label='Interview starten')

# Nutzungsbedingungen

st.title("Nutzungsbedingungen")

st.write("""
Bitte beachte die folgenden Nutzungsbedingungen:
            
Die Nutzung ist nur beschäftigten Personen der REWE Group im Rahmen ihrer beruflichen Tätigkeit gestattet.
Nicht gestattet ist die Verwendung von Inhalten und Eingabe von Daten, die als streng vertraulich zu klassifizieren sind. (Weitere Informationen in HORUS: Konzernrichtlinie zur Informationssicherheit, Anlage 1)
Die Eingabe und Anfrage von Hass-, sexuellen, Gewalt- oder Selbstverletzungsinhalten ist untersagt.
Die generierten Antworten sind nicht rechtsverbindlich, sondern dienen lediglich der ersten Information.
Die generierten Antworten können inkorrekt sein. Die weitere Verwendung der Antworten unterliegt sowohl deinem Urteilsvermögen als auch deiner Verantwortung.
Hinweis:
Das von Microsoft bereitgestellte GPT-Modell ist aktuell die Version GPT-4o (“o” for “omni”) von OpenAI.
Das öffentlich verfügbare Wissen wird von uns begrenzt, sodass die generierten Antworten nur aus den intern angereicherten Informationen aus den Lösungsartikeln generiert wird. Das Modell wird durch Eingaben nicht trainiert.
Solltest Du Fehler in den generierten Antworten feststellen, wende dich bitte an das Support Competence Center.
""")

