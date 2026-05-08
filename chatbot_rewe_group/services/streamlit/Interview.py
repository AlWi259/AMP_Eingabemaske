import streamlit as st
import utils.util_functions as util_functions


# Streamlit page title and icon configuration
st.set_page_config(
    page_title="Interview Assistant",
    layout="wide"
)

# Get client information (automatically uses email auth if available)
dev_mode, client_info = util_functions.get_client_information(st.context.headers)

# Initialize session state
if "job_id" not in st.session_state:
    st.session_state["job_id"] = ""
if "transcription" not in st.session_state:
    st.session_state["transcription"] = ""
if "yggs" not in st.session_state:
    st.session_state["yggs"] = []

with open('static/styles.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

st.sidebar.page_link('Interview.py', label='Startseite')
st.sidebar.page_link('pages/1_Interview_Assistant.py', label='Interview starten')


# --- HERO mit integrierter CTA rechts ---
st.markdown(f"""
<div class="hero">
  <div class="hero-inner">
    <div class="hero-content">
      <h1>Deine Erfahrung mit Microsoft 365 Copilot</h1>
      <p class="subtitle">
        Wir möchten verstehen, wie du den Microsoft 365 Copilot in deinem Arbeitsalltag nutzt. 
        Das Interview dauert rund 30 Minuten und deine Antworten werden vertraulich 
        und anonym ausgewertet.
      </p>
    </div>
  </div>
</div>
<div class="section-space"></div>
""", unsafe_allow_html=True)

# --- Steps ---
st.markdown(f"""
<div class="steps">
  <div class="step">
    <h3><span class="badge">1</span>Deine Erfahrungen teilen</h3>
    <p>Erzähle uns, wie du Microsoft 365 Copilot in deinem Arbeitsalltag nutzt und welche Erfahrungen du gemacht hast.</p>
  </div>
  <div class="step">
    <h3><span class="badge">2</span>Zusammenfassung überprüfen</h3>
    <p>Nach dem Interview kannst du deine Zusammenfassung durchlesen und bei Bedarf anpassen.</p>
  </div>
  <div class="step">
    <h3><span class="badge">3</span>Abschicken und fertig!</h3>
    <p>Mit einem Klick sendest du deine Rückmeldung ab – wir kümmern uns um den Rest.</p>
  </div>
</div>
""", unsafe_allow_html=True)

# CTA zentriert unter der Box
st.markdown('<div class="cta-row">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("▶ Interview starten", key="start", use_container_width=True):
        try:
            st.switch_page("pages/1_Interview_Assistant.py")
        except Exception:
            st.success("Öffnen Sie links in der Sidebar: **Interview Assistant**")
st.markdown('</div>', unsafe_allow_html=True)