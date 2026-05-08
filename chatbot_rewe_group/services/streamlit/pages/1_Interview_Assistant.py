import streamlit as st
from streamlit_float import *
from streamlit_js_eval import streamlit_js_eval
import uuid
import os
import time
import json
import html
from azure.identity import DefaultAzureCredential
import adapters.az_func_calls as az_func_calls
import utils.util_functions as util_functions
import rendering.render_elements as render_elements

credential = DefaultAzureCredential()
FUNCTION_AGENT_URL = os.environ.get("FUNCTION_AGENT_URL", "http://localhost:7071/api/interview_agent")
FUNCTION_YGG_URL = os.environ.get("FUNCTION_YGG_URL", "http://localhost:7071/api/generate_ygg")
DEV_MODE = os.environ.get("DEV_MODE", 0)
SIMULATION_MODE = os.environ.get("SIMULATION_MODE", 1)

st.set_page_config(page_title="Interview Assistant",
    layout="wide")

# inject_css("static/styles.css")

st.sidebar.page_link('Interview.py', label='Startseite')
st.sidebar.page_link('pages/1_Interview_Assistant.py', label='Interview starten')
st.session_state.simulation_mode = False
with open('static/styles.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
# st.markdown("""
# <div class="showcase-box">
#     <div class="showcase-box-icon">ℹ️</div>
#     <div class="showcase-box-text">
#     Dies ist ein <strong>Showcase</strong> für Demonstrationszwecke. 
#     Die Inhalte sind beispielhaft und dienen der Veranschaulichung.
#     </div>
# </div>
# """, unsafe_allow_html=True)

def initialize_session_state(client_info: dict) -> None:
    """Initialize all required session state variables with defaults if not present."""
    defaults = {
        "job_id": str(uuid.uuid4()),
        "user_id": client_info["principal_id"],
        "interview_id": "copilot",
        "simulation_iterations": 0,
        "interview_status": 0,
        "chat_history": [],
        "prompt": "",
        "llm_metadata": {
            "response_times": [],
            "prompt_tokens": [],
            "completion_tokens": []
        },
        "current_topic": "",
        "open_topics": [],
        "completed_topics": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def persona_builder() -> None:
    """Render the persona builder UI and update session state persona."""
    # Zeile 1: Rolle / Abteilung
    col1, col2 = st.columns(2)
    with col1:
        rollen_optionen = ["Sachbearbeitung", "Teamleitung", "Projektleitung", "Assistenz", "Geschäftsführung", "Andere (bitte angeben)"]
        ausgewählte_rolle = st.selectbox("👤 Rolle", rollen_optionen)
        if ausgewählte_rolle == "Andere (bitte angeben)":
            rolle = st.text_input("Eigene Rollenbezeichnung", placeholder="z. B. Innovationsmanager")
        else:
            rolle = ausgewählte_rolle
    with col2:
        abteilungen_optionen = ["IT", "HR", "Einkauf", "Vertrieb", "Finanzen", "Marketing", "Produktion", "Andere (bitte angeben)"]
        ausgewählte_abteilung = st.selectbox("🏢 Abteilung", abteilungen_optionen)
        if ausgewählte_abteilung == "Andere (bitte angeben)":
            abteilung = st.text_input("Eigene Abteilungsbezeichnung", placeholder="z. B. Innovationsmanagement")
        else:
            abteilung = ausgewählte_abteilung
    # Zeile 2: Erfahrung / Technische Affinität
    col3, col4 = st.columns(2)
    with col3:
        erfahrung = st.selectbox("📈 Erfahrungsebene", ["Junior", "Mid-Level", "Senior", "Leitung"])
    with col4:
        technische_affinitaet = st.radio("💻 Technische Affinität", ["niedrig", "mittel", "hoch"])
    # Zeile 3: Copilot-Nutzung / Haltung zu KI
    col5, col6 = st.columns(2)
    with col5:
        copilot_nutzung = st.selectbox("🤖 Copilot-Nutzung", ["keine", "ausprobiert", "gelegentlich", "regelmäßig", "täglich"])
    with col6:
        haltung_zu_ki = st.radio("🧠 Haltung zu KI", ["offen", "skeptisch", "abwartend", "begeistert"])
    # Tools (alleinstehend)
    tools = st.multiselect(
        "🛠️ Tools im Einsatz",
        ["Excel", "Outlook", "Teams", "PowerPoint", "Word", "SAP", "Dynamics", "Power BI", "SharePoint"],
        help="Welche Tools nutzt die Person typischerweise im Arbeitsalltag?"
    )
    # Gesprächshaltung (vordefiniert oder benutzerdefiniert)
    haltung_optionen = [
        "zurückhaltend und einsilbig",
        "neutral und sachlich",
        "offen und kommunikativ",
        "begeistert und ausführlich",
        "leicht genervt und abgelenkt",
        "skeptisch bis ablehnend",
        "Andere (bitte angeben)"
    ]
    ausgewählte_haltung = st.selectbox("🎭 Gesprächshaltung", haltung_optionen)
    if ausgewählte_haltung == "Andere (bitte angeben)":
        antwortstil = st.text_input("Eigene Beschreibung der Gesprächshaltung", placeholder="z. B. kurz angebunden aber ehrlich")
    else:
        antwortstil = ausgewählte_haltung
    st.selectbox(label="Simulations-Iterationen", options=list(range(1, 20)), key="max_iterations")
    # Persona zusammenstellen
    st.session_state.persona = {
        "name": "Max Mustermann",
        "role": rolle,
        "department": abteilung,
        "experience": erfahrung,
        "technical_affinity": technische_affinitaet,
        "tools": tools,
        "copilot_usage": copilot_nutzung,
        "ki_opinion": haltung_zu_ki,
        "answer_style": antwortstil
    }
    with st.expander("👁️ Persona-Vorschau"):
        st.json(st.session_state.persona)

def display_llm_metadata() -> None:
    """Display LLM metadata if in simulation mode."""
    with st.container(border=True):
        st.subheader("LLM-Metadaten")
        st.markdown("---")
        if len(st.session_state.llm_metadata["prompt_tokens"]) > 0:
            prompt_number = len(st.session_state.llm_metadata["prompt_tokens"])
            avg_prompt_tokens = sum(st.session_state.llm_metadata["prompt_tokens"]) / prompt_number
            avg_completion_tokens = sum(st.session_state.llm_metadata["completion_tokens"]) / prompt_number
            avg_response_time = sum(st.session_state.llm_metadata["response_times"]) / prompt_number
        else:
            prompt_number = 0
            avg_prompt_tokens = 0
            avg_completion_tokens = 0
            avg_response_time = 0
        st.write(f"Anzahl an Prompts: {prompt_number}")
        st.write(f"Durchschnittliche Prompt-Tokens: {avg_prompt_tokens}")
        st.write(f"Durchschnittliche Completion-Tokens: {avg_completion_tokens}")
        st.write(f"Durchschnittliche Antwortzeit: {round(avg_response_time, 2)} Sekunden")

def display_interview_report() -> None:
    """Display the final interview summary with edit and submit functionality."""

    if st.session_state.interview_status in [2, 3]:
        # Check if final summary has been submitted (saved to saved-data)
        final_summary_saved_blob = f"saved-data/final-summaries/{st.session_state.interview_id}-{st.session_state.user_id}-final_summary.json"
        saved_summary_data = None

        try:
            from adapters.az_blob_client import load_json_from_blob
            saved_summary_data = load_json_from_blob(final_summary_saved_blob)
            # Check if the loaded data actually contains a final_summary
            if not saved_summary_data or not saved_summary_data.get("final_summary"):
                saved_summary_data = None
        except:
            saved_summary_data = None

        # Display submitted (read-only) summary if already submitted (status 3 or saved data exists)
        if st.session_state.interview_status == 3 or (saved_summary_data and saved_summary_data.get("final_summary")):
            with st.container(border=True):
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.subheader("Abgeschickte Interview-Zusammenfassung")
                st.markdown("---")
                # Use saved data if available, otherwise use session state
                summary_content = saved_summary_data.get("final_summary") if saved_summary_data else st.session_state.get("final_summary", "")
                st.markdown(summary_content)

        # Display temporary (editable) summary if not yet submitted (status 2 and no saved data)
        elif st.session_state.interview_status == 2 and not saved_summary_data:
            final_summary_temp = st.session_state.get("final_summary", "")

            if final_summary_temp:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader("Interview-Zusammenfassung")

                    st.markdown("---")

                    # Calculate dynamic height based on content length (min 300, max 600)
                    line_count = final_summary_temp.count('\n') + 1
                    char_count = len(final_summary_temp)
                    estimated_lines = max(line_count, char_count // 80)  # Assume ~80 chars per line
                    dynamic_height = min(max(estimated_lines * 20 + 50, 300), 600)  # 20px per line + padding

                    content = st.text_area(
                        label="Schau dir deine Zusammenfassung an und passe sie gerne an, wenn du möchtest.",
                        value=final_summary_temp,
                        height=dynamic_height,
                        key="final_summary_content"
                    )

                    # Second submit button below text area
                    col_bottom1, col_bottom2, col_bottom3 = st.columns([2, 1, 2])
                    with col_bottom1:
                        if st.button("Abschicken", type="primary", use_container_width=True, key="submit_final_summary_bottom"):
                            content = st.session_state.get("final_summary_content", final_summary_temp)
                            try:
                                az_func_calls.save_final_summary(
                                    st.session_state.user_id,
                                    st.session_state.interview_id,
                                    content
                                )
                                st.rerun()
                            except Exception as e:
                                st.error("Beim Speichern ist etwas schiefgelaufen. Bitte versuche es noch einmal.")
            else:
                # Fallback if summary is still being generated
                st.info("Die Zusammenfassung wird generiert...")

def chat_logic() -> None:
    """Main chat logic and UI rendering."""
    if st.session_state.interview_status == 1:
        # Render existing chat history directly
        for msg in st.session_state.chat_history:
            avatar = "static/Element 20.png" if msg["role"] == "assistant" else "static/Element 21.png"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if st.session_state.simulation_mode and st.session_state.simulation_iterations < st.session_state.max_iterations:
            last_message = st.session_state.chat_history[-1]
            try:
                st.session_state.prompt = az_func_calls.simulate_user_response(
                    persona=st.session_state.persona,
                    last_question=last_message
                )
            except Exception as e:
                st.error(f"Fehler bei der Benutzersimulation: {e}")
                st.session_state.prompt = ""
            st.session_state.simulation_iterations += 1
            time.sleep(1)
        else:
            st.session_state.prompt = st.chat_input("Hier deine Antwort eingeben...")

        if st.session_state.prompt:
            message_without_comment, _ = util_functions.extract_meta_comment(st.session_state.prompt)
            print(f"Message without comment: {message_without_comment}")
            st.session_state.chat_history.append({"role": "user", "content": message_without_comment})

            with st.chat_message("user", avatar="static/Element 21.png"):
                st.markdown(message_without_comment)

            with st.chat_message("assistant", avatar="static/Element 20.png"):
                with st.spinner("Einen Moment..."):
                    start_time = time.perf_counter()
                    try:
                        ai_message, transition_text, llm_metadata, st.session_state.current_topic, st.session_state.open_topics, st.session_state.completed_topics, st.session_state.interview_status = az_func_calls.prompt_interview_agent(
                            st.session_state.prompt, st.session_state.user_id, st.session_state.interview_id)
                    except Exception as e:
                        st.error("Ups! Deine Antwort konnte nicht verarbeitet werden. Probiere es bitte noch einmal.")
                        ai_message, transition_text, llm_metadata = "", "", None
                    end_time = time.perf_counter()

                if transition_text:
                    st.markdown(transition_text)
                elif ai_message:
                    st.markdown(ai_message)

            if transition_text and ai_message:
                with st.chat_message("assistant", avatar="static/Element 20.png"):
                    st.markdown(ai_message)

            if transition_text:
                st.session_state.chat_history.append({"role": "assistant", "content": ai_message})
                st.session_state.chat_history.append({"role": "assistant", "content": transition_text})
            else:
                st.session_state.chat_history.append({"role": "assistant", "content": ai_message})

            # Generate final summary immediately when interview ends
            if st.session_state.interview_status == 2 and "interview_ended" not in st.session_state:
                st.session_state.interview_ended = True
                with st.spinner("Deine Zusammenfassung wird erstellt..."):
                    try:
                        final_summary = az_func_calls.generate_final_summary(
                            st.session_state.user_id,
                            st.session_state.interview_id
                        )
                        st.session_state.final_summary = final_summary
                        st.session_state.show_completion_modal = True
                    except Exception as e:
                        st.error("Ups! Etwas ist schiefgelaufen. Bitte lade die Seite neu oder kontaktiere uns, falls das Problem weiterhin besteht.")
                        st.session_state.show_completion_modal = True

            # Rerun if interview ended or in simulation mode
            if st.session_state.interview_status == 2 or st.session_state.simulation_mode:
                st.rerun()

    elif st.session_state.interview_status == 0:
        st.info("Willkommen! 👋 Lass uns über deine Erfahrungen mit Microsoft 365 Copilot sprechen.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Jetzt starten", type="primary", use_container_width=True):
                with st.spinner("Einen Moment..."):
                    st.session_state.prompt = ""
                    start_time = time.perf_counter()
                    try:
                        ai_message, transition_text, llm_metadata, st.session_state.current_topic, st.session_state.open_topics, st.session_state.completed_topics, st.session_state.interview_status = az_func_calls.prompt_interview_agent(
                            st.session_state.prompt, st.session_state.user_id, st.session_state.interview_id)
                    except Exception as e:
                        st.error("Hoppla! Das Interview konnte nicht gestartet werden. Bitte versuche es noch einmal oder melde dich bei uns.")
                        ai_message, llm_metadata = "", None
                    end_time = time.perf_counter()
                    if ai_message:
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_message})
                        st.rerun()

    elif st.session_state.interview_status == 2:
        st.success("Super gemacht! 🎉 Scrolle nach unten, um deine Zusammenfassung zu überprüfen und abzuschicken.")

        with st.expander("**Deine Antworten im Überblick**"):
            for msg in st.session_state.chat_history:
                avatar = "static/Element 20.png" if msg["role"] == "assistant" else "static/Element 21.png"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

    elif st.session_state.interview_status == 3:
        st.success("Perfekt! 🎉 Deine Zusammenfassung wurde erfolgreich abgeschickt. Vielen Dank für deine Teilnahme! Du kannst das Fenster jetzt schließen.")

        with st.expander("**Deine Antworten im Überblick**"):
            for msg in st.session_state.chat_history:
                avatar = "static/Element 20.png" if msg["role"] == "assistant" else "static/Element 21.png"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

def load_topics_config():
    """Load topics configuration from topics.json."""
    try:
        with open('topics.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Fehler beim Laden der Topics-Konfiguration: {e}")
        return None

def calculate_weighted_progress(completed_topics, current_topic):
    """Calculate progress based on probing budget weights from topics.json."""
    topics_config = load_topics_config()
    if not topics_config:
        # Fallback to simple calculation
        all_topics = completed_topics + [current_topic]
        return len(completed_topics) / len(all_topics) if all_topics else 0

    # Create mapping from topic scope to probing_limit
    topic_weights = {topic['scope']: topic['probing_limit'] for topic in topics_config['topics']}

    # Calculate total probing budget
    total_budget = sum(topic_weights.values())

    # Calculate completed budget
    completed_budget = sum(topic_weights.get(topic, 1) for topic in completed_topics)

    # Return progress ratio
    return completed_budget / total_budget if total_budget > 0 else 0

def display_interview_status() -> None:
    """Display the current interview status."""
    # Calculate weighted progress based on probing budget
    topic_completion_ratio = calculate_weighted_progress(
        st.session_state.completed_topics,
        st.session_state.current_topic
    )

    if st.session_state.interview_status == 1:
        all_topics = st.session_state.completed_topics + [st.session_state.current_topic] + st.session_state.open_topics
        with st.sidebar:
            st.markdown("---")
            st.markdown("<h3 style='margin-bottom: 0.2rem; margin-top: 0;'>Interview-Fortschritt</h3>", unsafe_allow_html=True)

            # Topics list with consistent spacing
            st.markdown("<div style='margin-bottom: 0.8rem; margin-top: 0;'>", unsafe_allow_html=True)
            for i, t in enumerate(all_topics, start=1):
                # Escape topic names to prevent XSS
                t_escaped = html.escape(str(t), quote=True)
                if t in st.session_state.completed_topics:
                    st.html(f"<p style='color: #707073; margin: 0.2rem 0;'><del>{i}. {t_escaped}</del></p>")
                elif t == st.session_state.current_topic:
                    st.html(f"<p style='margin: 0.2rem 0;'><strong>{i}. {t_escaped}</strong></p>")
                elif t in st.session_state.open_topics:
                    st.html(f"<p style='color: #707073; margin: 0.2rem 0;'>{i}. {t_escaped}</p>")
            st.markdown("</div>", unsafe_allow_html=True)

            # Custom progress bar with percentage (REWE CI colors)
            progress_percentage = int(topic_completion_ratio * 100)
            st.markdown(f"""
            <div style="width: 100%;">
                <div style="
                    position: relative;
                    width: 100%;
                    height: 35px;
                    background-color: #d1d3d4;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="
                        position: absolute;
                        left: 0;
                        top: 0;
                        height: 100%;
                        width: {progress_percentage}%;
                        background: linear-gradient(90deg, #cc071e 0%, #e63946 100%);
                        transition: width 0.3s ease;
                    "></div>
                    <div style="
                        position: absolute;
                        width: 100%;
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 1rem;
                        color: {'white' if progress_percentage > 45 else '#333'};
                        text-shadow: {'0 1px 2px rgba(0,0,0,0.2)' if progress_percentage > 45 else 'none'};
                    ">
                        {progress_percentage}%
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.interview_status in [2, 3]:
        with st.sidebar:
            st.markdown("---")
            st.markdown("<h3 style='margin-bottom: 0.2rem; margin-top: 0;'>Interview-Fortschritt</h3>", unsafe_allow_html=True)

            # Include current_topic if it exists and is not already in completed_topics
            all_completed_topics = st.session_state.completed_topics.copy()
            if st.session_state.current_topic and st.session_state.current_topic not in all_completed_topics:
                all_completed_topics.append(st.session_state.current_topic)

            for i, t in enumerate(all_completed_topics, start=1):
                # Escape topic names to prevent XSS
                t_escaped = html.escape(str(t), quote=True)
                st.html(f"<p style='color: #707073;text-decoration:line-through; margin: 0.2rem 0;'>{i}. {t_escaped}</p>")

            # 100% Progress bar for completed interview
            st.markdown("""
            <div style="width: 100%; margin-top: 0.8rem;">
                <div style="
                    position: relative;
                    width: 100%;
                    height: 35px;
                    background-color: #d1d3d4;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="
                        position: absolute;
                        left: 0;
                        top: 0;
                        height: 100%;
                        width: 100%;
                        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
                        transition: width 0.3s ease;
                    "></div>
                    <div style="
                        position: absolute;
                        width: 100%;
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 1rem;
                        color: white;
                        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
                    ">
                        100% ✓
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

            if st.session_state.interview_status == 2:
                st.write(f"Abgeschlossen: {len(all_completed_topics)} von {len(all_completed_topics)} Themenblöcken.")
            elif st.session_state.interview_status == 3:
                st.write(f"Abgeschlossen: {len(all_completed_topics)} von {len(all_completed_topics)} Themenblöcken.")

headers = st.context.headers
# Get client information (automatically uses email auth if available)
dev_mode, client_info = util_functions.get_client_information(headers=headers)
initialize_session_state(client_info)

st.markdown('<div class="interview-root">', unsafe_allow_html=True)

# Show loading indicator while fetching interview status
with st.spinner("Einen Moment bitte..."):
    try:
        st.session_state.chat_history, interview_status, st.session_state.current_topic, st.session_state.open_topics, st.session_state.completed_topics = az_func_calls.fetch_interview_status(st.session_state.user_id, st.session_state.interview_id)
        st.session_state.interview_status = interview_status
    except Exception as e:
        st.error(f"Fehler beim Laden des Interview-Status: {e}")
        st.session_state.chat_history = []
        st.session_state.interview_status = 0

if st.session_state.interview_status == 2:
    # Check if final summary already exists in session state
    if "interview_ended" not in st.session_state:
        st.session_state.interview_ended = True
        # Only generate if not already generated in chat_logic
        if "final_summary" not in st.session_state or not st.session_state.get("final_summary"):
            with st.spinner("Die finale Zusammenfassung wird generiert..."):
                try:
                    final_summary = az_func_calls.generate_final_summary(
                        st.session_state.user_id,
                        st.session_state.interview_id
                    )
                    st.session_state.final_summary = final_summary
                    st.session_state.show_completion_modal = True
                except Exception as e:
                    st.error(f"Fehler beim Generieren der finalen Zusammenfassung: {e}")
                    st.session_state.show_completion_modal = True
        else:
            # Final summary already generated, just show modal
            if "show_completion_modal" not in st.session_state:
                st.session_state.show_completion_modal = True
    else:
        st.session_state.interview_ended = True

elif st.session_state.interview_status == 3:
    # Interview completed and final summary submitted
    if "interview_fully_completed" not in st.session_state:
        st.session_state.interview_fully_completed = True
        # Load the saved final summary
        with st.spinner("Lade Zusammenfassung..."):
            try:
                final_summary = az_func_calls.generate_final_summary(
                    st.session_state.user_id,
                    st.session_state.interview_id
                )
                st.session_state.final_summary = final_summary
            except Exception as e:
                st.error(f"Fehler beim Laden der finalen Zusammenfassung: {e}")
    else:
        st.session_state.interview_fully_completed = True

st.markdown("## Interview zu deiner Erfahrung mit Microsoft 365 Copilot")
# if st.session_state.interview_status in [0, 1]:
#     st.caption("💡 Tipp: Du kannst Meta-Kommentare im Format `### Kommentar ###` eingeben, um zusätzliches Feedback zu geben.")

# Show completion modal when interview ends
if st.session_state.get("show_completion_modal", False):
    @st.dialog("Geschafft! 🎉", width="large")
    def show_completion_instructions():
        st.markdown("Super! Deine Antworten wurden erfolgreich erfasst.")

        st.markdown("""
        ### Noch ein letzter Schritt

        Wir haben deine Antworten zu einer Zusammenfassung zusammengefasst.

        **Bitte überprüfe sie kurz:**
        - Scrolle nach unten zur **"Interview-Zusammenfassung"**
        - Lies sie durch und passe sie bei Bedarf an
        - Klicke auf **"Abschicken"**, wenn alles passt

        💡 **Wichtig:** Nach dem Abschicken kannst du die Zusammenfassung nicht mehr ändern.
        """)

        if st.button("Alles klar!", type="primary", use_container_width=True):
            st.session_state.show_completion_modal = False
            st.rerun()

    show_completion_instructions()

# if SIMULATION_MODE:
#     st.checkbox("Simulationsmodus aktivieren", key="simulation_mode")
# else:
#     st.session_state.simulation_mode = False
# if st.session_state.simulation_mode:
#     persona_builder()
# if st.sidebar.button("Interview-Historie löschen"):
#     with st.spinner("Lösche Interview-Historie..."):
#         try:
#             az_func_calls.delete_interview_history(st.session_state.user_id, st.session_state.interview_id)
#         except Exception as e:
#             st.error(f"Fehler beim Löschen der Interview-Historie: {e}")
#     streamlit_js_eval(js_expressions="parent.window.location.reload()")

if st.session_state.interview_status in [0, 1, 2, 3]:
    chat_logic()
else:
    # Inform the user that the interview assistant is not reachable
    st.error("Interview-Assistent nicht erreichbar.")

# if DEV_MODE:
#     display_llm_metadata()

display_interview_status()
if not st.session_state.interview_status == 0 or st.session_state.interview_status is not None:
    display_interview_report()

st.markdown('</div>', unsafe_allow_html=True)