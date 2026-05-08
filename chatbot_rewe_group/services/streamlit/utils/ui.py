# lib/ui.py
from pathlib import Path
import streamlit as st

@st.cache_resource
def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def inject_css(filename: str = "static/styles.css"):
    # robust: funktioniert sowohl in / als auch in /pages
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / filename,  # wenn diese Datei in /lib liegt
        here.parent / filename,         # wenn styles.css neben der Seite liegt
        Path.cwd() / filename,          # fallback: Working Directory
    ]
    
    for p in candidates:
        if p.exists():
            css = _read_text(p)
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            print(f"CSS-Datei erfolgreich geladen: {p}")
            return
    st.warning(f"CSS-Datei nicht gefunden: {filename}")