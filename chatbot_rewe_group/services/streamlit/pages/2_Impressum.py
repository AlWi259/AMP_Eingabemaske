import streamlit as st

from utils.ui import inject_css

# Streamlit page title and icon configuration
st.set_page_config(
    page_title="Interview Assistant - Impressum",
)

inject_css("static/styles.css")

st.sidebar.page_link('Interview.py', label='Startseite')
st.sidebar.page_link('pages/1_Interview_Assistant.py', label='Interview starten')

# Impressum
# This is a placeholder Impressum for the application.
# Please replace the following details with actual information.

st.title("Impressum")

st.write("""
**Angaben gemäss § 5 TMG:**

ADVIA GmbH\n
Phoenixplatz 2b\n
44263 Dortmund

**Vertreten durch:**

Geschäftsführer:
Dipl.-Ing. Martin Behn
Dipl.-Kfm. Christian Spraetz

**Kontakt:**

Telefon: +49 231 398190-40
Telefax: +49 231 398190-49
E-Mail: info@advia.de

**Registereintrag:**

Eintragung im Handelsregister.\n
Registergericht: Dortmund\n
Registernummer: HRB 27729\n

Ust-ID: DE268236731

**Verantwortlich für den Inhalt nach § 5 Abs. 2 RSTV:**

Martin Behn\n
ADVIA GMBH\n
Phoenixplatz 2b\n
44263 Dortmund\n

**Streitschlichtung**

Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.

**Haftung für Inhalte**

Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.

Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.

**Urheberrecht**

Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet.

Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.
""")

