const THEME_KEY = "berichtskatalog-theme";
const API_BASE_URL =
  window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : `${window.location.origin}/api`;

const CHAT_GREETING =
  "Guten Tag! Ich nehme heute Ihren Bericht für den Katalog auf. " +
  "Fangen wir direkt an: Wie heißt der Bericht, den wir heute erfassen?";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let recognizing = false;

const fieldDefinitions = [
  {
    key: "berichtId",
    exportLabel: "Bericht-ID",
    label: "Bericht-ID",
    type: "text",
    category: "Identifikation",
    required: false,
    defaultValue: "-",
    placeholder: "z. B. REP-2048",
  },
  {
    key: "berichtsname",
    exportLabel: "Berichtsname",
    label: "Berichtsname",
    type: "text",
    category: "Identifikation",
    required: true,
    placeholder: "z. B. Vertriebsdashboard Deutschland",
  },
  {
    key: "beschreibung",
    exportLabel: "Beschreibung",
    label: "Beschreibung",
    type: "textarea",
    category: "Identifikation",
    required: true,
    placeholder: "Kurz die Nutzung und den Inhalt beschreiben",
  },
  {
    key: "workspace",
    exportLabel: "Workspace / Ablageort",
    label: "Workspace / Ablageort",
    type: "text",
    category: "Identifikation",
    required: false,
    defaultValue: "-",
    placeholder: "z. B. BI Reporting / Vertrieb",
  },
  {
    key: "berichtstyp",
    exportLabel: "Berichtstyp",
    label: "Berichtstyp",
    type: "select",
    category: "Identifikation",
    required: true,
    options: [
      "Operativer Bericht",
      "Managementbericht",
      "Finanzbericht",
      "Dashboard",
      "Ad-hoc-Analyse",
      "KPI-Übersicht",
      "Regulatorischer Bericht",
      "Forecast / Prognose",
      "Sonstiges",
    ],
  },
  {
    key: "besitzer",
    exportLabel: "Besitzer",
    label: "Besitzer",
    type: "text",
    category: "Verantwortung",
    required: true,
    placeholder: "z. B. Anna Beispiel",
  },
  {
    key: "fachabteilung",
    exportLabel: "Fachabteilung",
    label: "Fachabteilung",
    type: "select",
    category: "Verantwortung",
    required: true,
    options: [
      "Controlling",
      "Finanzen",
      "Vertrieb",
      "Marketing",
      "Einkauf",
      "Logistik",
      "Produktion",
      "Personal / HR",
      "IT",
      "Geschäftsführung",
      "Qualitätssicherung",
      "Rechtswesen",
      "Sonstiges",
    ],
  },
  {
    key: "itAnsprechpartner",
    exportLabel: "IT-Ansprechpartner",
    label: "IT-Ansprechpartner",
    type: "text",
    category: "Verantwortung",
    required: true,
    placeholder: "z. B. Max Mustermann",
  },
  {
    key: "primaereDatenquelle",
    exportLabel: "Primäre Datenquelle",
    label: "Primäre Datenquelle",
    type: "select",
    category: "Technologie & Daten",
    required: true,
    options: [
      "SQL Server",
      "Power BI Dataflow",
      "Oracle",
      "SAP HANA",
      "MySQL",
      "PostgreSQL",
      "Azure SQL",
      "Snowflake",
      "BigQuery",
      "Excel / CSV",
      "SharePoint-Liste",
      "REST API",
      "OData",
      "SAP BW",
      "Sonstiges",
    ],
  },
  {
    key: "weitereDatenquellen",
    exportLabel: "Weitere Datenquellen",
    label: "Weitere Datenquellen",
    type: "textarea",
    category: "Technologie & Daten",
    required: false,
    defaultValue: "-",
    placeholder: "z. B. Excel / CSV, REST API",
  },
  {
    key: "aktuellesTool",
    exportLabel: "Aktuelles Tool",
    label: "Aktuelles Tool",
    type: "select",
    category: "Technologie & Daten",
    required: true,
    options: ["Excel", "Power BI", "SSRS", "Tableau", "Qlik", "IBM Cognos", "Sonstiges"],
  },
  {
    key: "ausgabeformat",
    exportLabel: "Ausgabeformat",
    label: "Ausgabeformat",
    type: "select",
    category: "Technologie & Daten",
    required: true,
    options: [
      "Excel (.xlsx)",
      "Power BI Report",
      "Power BI App",
      "PDF",
      "PowerPoint",
      "Web-Browser / URL",
      "E-Mail",
      "SharePoint-Seite",
      "Confluence",
      "Microsoft Teams",
      "CSV / Text",
      "Sonstiges",
    ],
  },
  {
    key: "zielgruppe",
    exportLabel: "Zielgruppe",
    label: "Zielgruppe",
    type: "select",
    category: "Technologie & Daten",
    required: true,
    options: ["Management", "Fachabteilung", "Analysten", "Externe Stakeholder"],
  },
  {
    key: "parameterFilter",
    exportLabel: "Parameter / Filter",
    label: "Parameter / Filter",
    type: "text",
    category: "Technologie & Daten",
    required: false,
    defaultValue: "Keine",
    placeholder: "z. B. Zeitraum, Region, Kostenstelle",
  },
  {
    key: "gatewayVerbindungen",
    exportLabel: "Gateway-Verbindungen",
    label: "Gateway-Verbindungen",
    type: "select",
    category: "Technologie & Daten",
    required: true,
    options: ["Ja", "Nein", "Unbekannt"],
  },
  {
    key: "automatisierungsgrad",
    exportLabel: "Automatisierungsgrad",
    label: "Automatisierungsgrad",
    type: "select",
    category: "Qualität & Betrieb",
    required: true,
    options: ["Vollautomatisiert", "Teilautomatisiert", "Manuell"],
  },
  {
    key: "manuellerAufwand",
    exportLabel: "Manueller Aufwand",
    label: "Manueller Aufwand (Pre-report)",
    type: "select",
    category: "Qualität & Betrieb",
    required: true,
    options: ["Kein Aufwand", "Stunden", "Tage", "Wochen"],
  },
  {
    key: "aufwandKonkret",
    exportLabel: "Aufwand konkret",
    label: "Aufwand konkret",
    type: "textarea",
    category: "Qualität & Betrieb",
    required: false,
    defaultValue: "-",
    placeholder: "Welche manuellen Schritte sind vor dem Reporting notwendig?",
    dependsOn: {
      key: "manuellerAufwand",
      values: ["Stunden", "Tage", "Wochen"],
    },
  },
  {
    key: "aktualisierungsfrequenz",
    exportLabel: "Aktualisierungsfrequenz",
    label: "Aktualisierungsfrequenz",
    type: "select",
    category: "Qualität & Betrieb",
    required: true,
    options: [
      "Echtzeit",
      "Stündlich",
      "Täglich",
      "Wöchentlich",
      "14-tägig",
      "Monatlich",
      "Quartalsweise",
      "Halbjährlich",
      "Jährlich",
      "On-Demand",
    ],
  },
  {
    key: "datenaktualitaet",
    exportLabel: "Datenaktualität",
    label: "Datenaktualität",
    type: "select",
    category: "Qualität & Betrieb",
    required: true,
    defaultValue: "Aktuell",
    options: ["Aktuell", "Veraltet"],
  },
  {
    key: "approvalNachAenderung",
    exportLabel: "Approval nach Änderung",
    label: "Approval nach Änderung",
    type: "select",
    category: "Qualität & Betrieb",
    required: true,
    options: ["Kein Approval", "Fachbereich", "Management", "Regulatorisch"],
  },
  {
    key: "letztesReview",
    exportLabel: "Letztes Review",
    label: "Letztes Review",
    type: "monthText",
    category: "Qualität & Betrieb",
    required: true,
    defaultValue: "03.2025",
    placeholder: "z. B. 03.2025",
  },
  {
    key: "komplexitaet",
    exportLabel: "Komplexität",
    label: "Komplexität",
    type: "select",
    category: "Power BI Migration",
    required: true,
    options: ["Niedrig", "Mittel", "Hoch", "Sehr hoch"],
  },
  {
    key: "migrationsstatus",
    exportLabel: "Migrationsstatus",
    label: "Migrationsstatus",
    type: "select",
    category: "Power BI Migration",
    required: true,
    defaultValue: "Offen",
    options: [
      "Offen",
      "In Analyse",
      "In Entwicklung",
      "In Review / Test",
      "Abgeschlossen",
      "Zurückgestellt",
      "Nicht migrieren",
    ],
  },
  {
    key: "prioritaet",
    exportLabel: "Priorität",
    label: "Priorität",
    type: "select",
    category: "Priorisierung",
    required: true,
    options: ["Kritisch", "Hoch", "Mittel", "Niedrig"],
  },
  {
    key: "aufwandPt",
    exportLabel: "Aufwand (PT)",
    label: "Aufwand (PT)",
    type: "number",
    category: "Priorisierung",
    required: false,
    defaultValue: "-",
    placeholder: "z. B. 8",
  },
  {
    key: "bemerkungen",
    exportLabel: "Bemerkungen",
    label: "Bemerkungen",
    type: "textarea",
    category: "Notizen",
    required: false,
    defaultValue: "-",
    placeholder: "Weitere Hinweise",
  },
];

const assistantContent = document.querySelector("#assistant-content");
const savedEntriesContainer = document.querySelector("#saved-entries");
const themeToggle = document.querySelector("#theme-toggle");
const appNav = document.querySelector("#app-nav");
const tabChat = document.querySelector("#tab-chat");
const tabEntries = document.querySelector("#tab-entries");

const appState = {
  values: buildInitialValues(),
  otherDetails: {},
  savedEntries: [],
  savedEntriesLoaded: false,
  savedEntriesError: "",
  theme: loadTheme(),
  status: { message: "", variant: "success" },
  lastSavedSignature: "",
  mode: "chat",
  chatMessages: [],
  chatLoading: false,
  chatStreamingText: "",
  collectedFields: {},
  auditNote: "",
  partialEntryId: null,
  completionOrigin: "chat",
  _restoredFromSession: false,
};

applyTheme(appState.theme);
tryRestoreSession();
themeToggle.addEventListener("click", toggleTheme);
appNav.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-tab]");
  if (!btn) return;
  const tab = btn.dataset.tab;
  appNav.querySelectorAll(".app-nav__tab").forEach((t) => t.classList.remove("app-nav__tab--active"));
  btn.classList.add("app-nav__tab--active");
  tabChat.hidden = tab !== "chat";
  tabEntries.hidden = tab !== "entries";
  if (tab === "entries") renderSavedEntries();
});
render();
void initializeSavedEntries();

function buildInitialValues() {
  return fieldDefinitions.reduce((accumulator, field) => {
    accumulator[field.key] = field.defaultValue ?? "";
    return accumulator;
  }, {});
}

async function initializeSavedEntries() {
  try {
    appState.savedEntries = await fetchSavedEntries();
    appState.savedEntriesError = "";
  } catch (error) {
    appState.savedEntries = [];
    appState.savedEntriesError =
      "Gespeicherte Berichte konnten nicht geladen werden. Bitte den lokalen Server starten.";
  }

  appState.savedEntriesLoaded = true;
  renderSavedEntries();
}

async function fetchSavedEntries() {
  const data = await requestJson(`${API_BASE_URL}/reports`);
  return Array.isArray(data.entries) ? data.entries : [];
}

async function createSavedEntry(entry) {
  const data = await requestJson(`${API_BASE_URL}/reports`, {
    method: "POST",
    body: JSON.stringify(entry),
  });
  return data.entry;
}

async function removeSavedEntry(entryId) {
  await requestJson(`${API_BASE_URL}/reports/${encodeURIComponent(entryId)}`, {
    method: "DELETE",
  });
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const error = new Error(payload?.error || "Server request failed.");
    error.status = response.status;
    throw error;
  }

  return payload ?? {};
}

function loadTheme() {
  try {
    const stored = window.localStorage.getItem(THEME_KEY);
    if (stored === "light" || stored === "dark") {
      return stored;
    }
  } catch (error) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.setAttribute("aria-checked", String(theme === "dark"));
}

function toggleTheme() {
  appState.theme = appState.theme === "dark" ? "light" : "dark";
  try {
    window.localStorage.setItem(THEME_KEY, appState.theme);
  } catch (error) {
    // theme still changes even if storage is blocked
  }
  applyTheme(appState.theme);
}

function getVisibleFields() {
  return fieldDefinitions.filter((field) => {
    if (!field.dependsOn) {
      return true;
    }
    return field.dependsOn.values.includes(appState.values[field.dependsOn.key]);
  });
}

function render() {
  if (appState.mode === "complete") {
    renderCompletion();
  } else {
    renderChat();
  }
  renderSavedEntries();
}

// ---------------------------------------------------------------------------
// Chat mode
// ---------------------------------------------------------------------------

function renderChatMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
  return html;
}

function renderChat() {
  const hasMic = Boolean(SpeechRecognition);

  assistantContent.innerHTML = `
    <div class="chat-container">
      ${appState._restoredFromSession ? `
        <div class="chat-restore-banner">
          Erfassung wiederhergestellt.
          <button type="button" class="chat-restore-discard" id="discard-session-btn">Neu starten</button>
        </div>` : ""}
      <div class="chat-messages" id="chat-messages">
        <div class="chat-bubble chat-bubble--assistant">${renderChatMarkdown(CHAT_GREETING)}</div>
        ${appState.chatMessages
          .map((m) => {
            const content = m.role === "assistant" ? renderChatMarkdown(m.content) : escapeHtml(m.content);
            return `<div class="chat-bubble chat-bubble--${escapeAttribute(m.role)}">${content}</div>`;
          })
          .join("")}
        ${
          appState.chatLoading
            ? appState.chatStreamingText
              ? `<div class="chat-bubble chat-bubble--assistant chat-bubble--streaming">${renderChatMarkdown(appState.chatStreamingText)}</div>`
              : `<div class="chat-typing">
                  <span class="chat-typing__dot"></span>
                  <span class="chat-typing__dot"></span>
                  <span class="chat-typing__dot"></span>
                 </div>`
            : ""
        }
      </div>
      <div class="chat-end-row">
        <button type="button" class="chat-save-partial-btn" id="chat-save-partial-button" ${appState.chatLoading ? "disabled" : ""}>Zwischenspeichern</button>
        <button type="button" class="chat-end-btn" id="chat-end-button">Erfassung abbrechen</button>
      </div>
      <form class="chat-input-row" id="chat-form" ${appState.chatLoading ? "inert" : ""}>
        <textarea
          id="chat-input"
          placeholder="Antwort eingeben …"
          rows="1"
          ${appState.chatLoading ? "disabled" : ""}
        ></textarea>
        ${
          hasMic
            ? `<button type="button" class="chat-mic-btn" id="mic-button" aria-label="Spracheingabe" title="Spracheingabe">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <rect x="5.5" y="0.5" width="5" height="9" rx="2.5" stroke="currentColor" stroke-width="1" fill="none"/>
                  <path d="M2.5 8a5.5 5.5 0 0010 0" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>
                  <line x1="8" y1="13.5" x2="8" y2="15.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
               </button>`
            : ""
        }
        <button type="submit" class="chat-send-btn" aria-label="Senden">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M15.5 9L3 15.5V11L11 9L3 7V2.5L15.5 9Z"/>
          </svg>
        </button>
      </form>
    </div>
  `;

  const messagesEl = document.querySelector("#chat-messages");
  if (messagesEl) {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  const form = document.querySelector("#chat-form");
  const input = document.querySelector("#chat-input");
  const micBtn = document.querySelector("#mic-button");

  if (form) {
    form.addEventListener("submit", handleChatSubmit);
  }

  const endBtn = document.querySelector("#chat-end-button");
  if (endBtn) {
    endBtn.addEventListener("click", async () => {
      if (!window.confirm("Erfassung wirklich abbrechen? Alle bisherigen Eingaben gehen verloren.")) return;
      if (appState.partialEntryId) {
        try { await removeSavedEntry(appState.partialEntryId); } catch (_) {}
      }
      appState.mode = "chat";
      appState.chatMessages = [];
      appState.chatLoading = false;
      appState.chatStreamingText = "";
      appState.collectedFields = {};
      appState.auditNote = "";
      appState.partialEntryId = null;
      appState._restoredFromSession = false;
      appState.values = buildInitialValues();
      appState.otherDetails = {};
      clearSaveFeedback();
      clearSession();
      render();
    });
  }

  const savePartialBtn = document.querySelector("#chat-save-partial-button");
  if (savePartialBtn) {
    savePartialBtn.addEventListener("click", () => handleSavePartial(savePartialBtn));
  }

  const discardBtn = document.querySelector("#discard-session-btn");
  if (discardBtn) {
    discardBtn.addEventListener("click", async () => {
      if (appState.partialEntryId) {
        try { await removeSavedEntry(appState.partialEntryId); } catch (_) {}
      }
      appState.chatMessages = [];
      appState.collectedFields = {};
      appState.auditNote = "";
      appState.partialEntryId = null;
      appState._restoredFromSession = false;
      appState.values = buildInitialValues();
      clearSession();
      render();
    });
  }

  if (input) {
    autoResizeTextarea(input);
    input.addEventListener("input", () => autoResizeTextarea(input));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form?.requestSubmit();
      }
    });
    if (!appState.chatLoading) {
      input.focus();
    }
  }

  if (micBtn && hasMic) {
    if (recognizing) micBtn.classList.add("chat-mic-btn--active");
    attachMicEvents(micBtn, input, form);
  }

}

// ---------------------------------------------------------------------------
// Microphone – tap to toggle, hold to push-to-talk; both auto-send on result
// ---------------------------------------------------------------------------

let micHoldTimer = null;
let micHoldMode = false;
let micTapMode = false;

function attachMicEvents(btn, inputEl, formEl) {
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    btn.setPointerCapture(e.pointerId);

    if (micTapMode && recognizing) {
      // Second tap → stop, result will auto-send
      recognition.stop();
      return;
    }

    if (!recognizing) {
      micHoldMode = false;
      micTapMode = false;
      startMicRecognition(inputEl, formEl);
      micHoldTimer = window.setTimeout(() => { micHoldMode = true; }, 350);
    }
  });

  btn.addEventListener("pointerup", () => {
    window.clearTimeout(micHoldTimer);
    if (micHoldMode && recognizing) {
      // Hold release → stop, result will auto-send
      micHoldMode = false;
      recognition.stop();
    } else if (!micHoldMode && recognizing) {
      // Quick tap → stay recording (tap mode)
      micTapMode = true;
    }
  });

  btn.addEventListener("contextmenu", (e) => e.preventDefault());
}

function startMicRecognition(inputEl, formEl) {
  recognition = new SpeechRecognition();
  recognition.lang = "de-DE";
  recognition.interimResults = false;
  recognition.continuous = true;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    recognizing = true;
    document.querySelector("#mic-button")?.classList.add("chat-mic-btn--active");
  };

  recognition.onend = () => {
    recognizing = false;
    micTapMode = false;
    micHoldMode = false;
    document.querySelector("#mic-button")?.classList.remove("chat-mic-btn--active");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript;
    recognition.stop();
    const input = document.querySelector("#chat-input");
    if (input) {
      input.value = (input.value ? input.value + " " : "") + transcript;
      autoResizeTextarea(input);
    }
    window.setTimeout(() => formEl?.requestSubmit(), 60);
  };

  recognition.onerror = () => {
    recognizing = false;
    micTapMode = false;
    micHoldMode = false;
    document.querySelector("#mic-button")?.classList.remove("chat-mic-btn--active");
  };

  recognition.start();
}

function _chatAppendBubble(role, html) {
  const msgs = document.querySelector("#chat-messages");
  if (!msgs) return null;
  const el = document.createElement("div");
  el.className = `chat-bubble chat-bubble--${role}`;
  el.innerHTML = html;
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
  return el;
}

function _chatShowLoading() {
  const msgs = document.querySelector("#chat-messages");
  if (!msgs) return;
  const el = document.createElement("div");
  el.className = "chat-typing";
  el.innerHTML = '<span class="chat-typing__dot"></span><span class="chat-typing__dot"></span><span class="chat-typing__dot"></span>';
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
  const form = document.querySelector("#chat-form");
  if (form) form.inert = true;
  const input = document.querySelector("#chat-input");
  if (input) { input.disabled = true; input.value = ""; autoResizeTextarea(input); }
}

function _chatFinalize(complete) {
  // Remove blinking cursor from streaming bubble
  document.querySelector(".chat-bubble--streaming")?.classList.remove("chat-bubble--streaming");

  if (complete) {
    render();
    return;
  }

  const form = document.querySelector("#chat-form");
  if (form) form.inert = false;
  const input = document.querySelector("#chat-input");
  if (input) { input.disabled = false; input.focus(); }
}

function _chatShowError(msg) {
  document.querySelector(".chat-typing")?.remove();
  document.querySelector(".chat-bubble--streaming")?.remove();
  _chatAppendBubble("assistant", escapeHtml(msg));
  const form = document.querySelector("#chat-form");
  if (form) form.inert = false;
  const input = document.querySelector("#chat-input");
  if (input) { input.disabled = false; input.focus(); }
}

async function handleChatSubmit(event) {
  event.preventDefault();

  const input = document.querySelector("#chat-input");
  const text = input ? input.value.trim() : "";
  if (!text || appState.chatLoading) return;

  appState.chatMessages.push({ role: "user", content: text });
  appState.chatLoading = true;
  appState.chatStreamingText = "";

  _chatAppendBubble("user", escapeHtml(text));
  _chatShowLoading();

  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({
        messages: appState.chatMessages,
        collectedFields: appState.collectedFields,
        auditNote: appState.auditNote,
      }),
    });

    if (!response.ok) {
      const err = new Error(`HTTP ${response.status}`);
      err.status = response.status;
      throw err;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        let ev;
        try { ev = JSON.parse(jsonStr); } catch { continue; }

        if (ev.type === "delta") {
          appState.chatStreamingText += ev.text;
          let bubble = document.querySelector(".chat-bubble--streaming");
          if (!bubble) {
            const typingDots = document.querySelector(".chat-typing");
            bubble = document.createElement("div");
            bubble.className = "chat-bubble chat-bubble--assistant chat-bubble--streaming";
            if (typingDots) {
              typingDots.replaceWith(bubble);
            } else {
              document.querySelector("#chat-messages")?.appendChild(bubble);
            }
          }
          bubble.innerHTML = renderChatMarkdown(appState.chatStreamingText);
          const msgs = document.querySelector("#chat-messages");
          if (msgs) msgs.scrollTop = msgs.scrollHeight;

        } else if (ev.type === "done") {
          if (ev.collectedFields && typeof ev.collectedFields === "object") {
            appState.collectedFields = ev.collectedFields;
            appState.values = { ...buildInitialValues(), ...ev.collectedFields };
          }
          appState.auditNote = ev.auditNote || "";
          const finalText = appState.chatStreamingText.trim() || "Ich habe Ihre Antwort verarbeitet.";
          appState.chatMessages.push({ role: "assistant", content: finalText });
          appState.chatStreamingText = "";
          if (ev.complete) {
            appState.mode = "complete";
            appState.completionOrigin = "chat";
            clearSession();
            // Auto-delete partial entry from DB now that interview is complete
            if (appState.partialEntryId) {
              const oldPartialId = appState.partialEntryId;
              appState.partialEntryId = null;
              removeSavedEntry(oldPartialId).then(() => {
                appState.savedEntries = appState.savedEntries.filter((e) => e.id !== oldPartialId);
              }).catch(() => {});
            }
          } else {
            saveSession();
          }

        } else if (ev.type === "error") {
          const errMsg = ev.message || "Ein Fehler ist aufgetreten.";
          appState.chatMessages.push({ role: "assistant", content: errMsg });
          appState.chatStreamingText = "";
          _chatShowError(errMsg);
        }
      }
    }
  } catch (error) {
    const msg =
      error.status === 503
        ? "ANTHROPIC_API_KEY fehlt oder ist ungültig. Bitte in der .env-Datei setzen und Server neu starten."
        : "Entschuldigung, es ist ein Fehler aufgetreten. Bitte erneut versuchen.";
    appState.chatMessages.push({ role: "assistant", content: msg });
    appState.chatStreamingText = "";
    _chatShowError(msg);
    appState.chatLoading = false;
    return;
  }

  appState.chatLoading = false;
  _chatFinalize(appState.mode === "complete");
  if (appState.mode === "complete") {
    _autoSaveReport();
  }
}

// ---------------------------------------------------------------------------
// Auto-save on interview completion
// ---------------------------------------------------------------------------

async function _autoSaveReport() {
  const exportMarkdown = buildExportMarkdown();
  const signature = exportMarkdown;

  // Already saved (e.g. duplicate call)
  if (appState.lastSavedSignature === signature) return;

  const summary = buildNormalizedSummary();
  const payload = {
    signature,
    name: summary.berichtsname || "Unbenannter Bericht",
    fachabteilung: summary.fachabteilung || "-",
    timestamp: new Date().toLocaleString("de-DE"),
    exportMarkdown,
    summary,
    complete: true,
  };

  try {
    const savedEntry = await createSavedEntry(payload);
    appState.savedEntries.unshift(savedEntry);
    appState.savedEntriesError = "";
    appState.lastSavedSignature = signature;
    // Clean up any remaining partial entry
    if (appState.partialEntryId) {
      const oldId = appState.partialEntryId;
      appState.partialEntryId = null;
      appState.savedEntries = appState.savedEntries.filter((e) => e.id !== oldId);
      removeSavedEntry(oldId).catch(() => {});
    }
    // Refresh completion screen so "Speichern" button shows as already saved
    if (appState.mode === "complete") render();
  } catch (error) {
    if (error.status === 409) {
      // Already in DB — mark locally as saved
      appState.lastSavedSignature = signature;
      if (appState.mode === "complete") render();
    }
    // Other errors: silent — user can still manually save via the button
  }
}

// ---------------------------------------------------------------------------
// Partial save (Zwischenspeichern)
// ---------------------------------------------------------------------------

async function handleSavePartial(btn) {
  if (appState.chatMessages.length === 0) return;
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Wird gespeichert…";

  try {
    // Remove previous partial entry for this session before creating a new one
    if (appState.partialEntryId) {
      try { await removeSavedEntry(appState.partialEntryId); } catch (_) {}
      appState.partialEntryId = null;
    }

    const name = appState.collectedFields.berichtsname || "Laufende Erfassung";
    const fachabteilung = appState.collectedFields.fachabteilung || "-";
    const sig = "partial_" + generateId();

    const entry = await createSavedEntry({
      signature: sig,
      name,
      fachabteilung,
      timestamp: new Date().toLocaleString("de-DE"),
      exportMarkdown: buildExportMarkdown(),
      summary: appState.collectedFields,
      complete: false,
      chatMessages: appState.chatMessages,
      auditNote: appState.auditNote,
    });

    appState.partialEntryId = entry.id;
    appState.savedEntries = [entry, ...appState.savedEntries.filter((e) => e.id !== entry.id)];
    saveSession();

    btn.textContent = "Gespeichert ✓";
    window.setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
    }, 1800);
  } catch (_) {
    btn.textContent = "Fehler";
    window.setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
    }, 1800);
  }
}

function generateId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

// ---------------------------------------------------------------------------
// Completion screen
// ---------------------------------------------------------------------------

function renderCompletion() {
  const exportMarkdown = buildExportMarkdown();
  const signature = exportMarkdown;
  const alreadySaved = appState.lastSavedSignature === signature;

  assistantContent.innerHTML = `
    <article class="completion-card">
      <h2>Zusammenfassung</h2>
      <p class="completion-card__copy">
        Eingabe abgeschlossen. Speichern, kopieren oder als Markdown exportieren.
      </p>

      <div class="summary-export">
        <div class="summary-export__toolbar">
          <button type="button" class="summary-copy-btn" id="copy-button" aria-label="Markdown kopieren">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect x="4.5" y="0.5" width="10" height="10" rx="1.5" stroke="currentColor"/>
              <path d="M2 4H1.5A1.5 1.5 0 000 5.5v8A1.5 1.5 0 001.5 15h8A1.5 1.5 0 0011 13.5V13H9.5v.5a.5.5 0 01-.5.5h-8a.5.5 0 01-.5-.5v-8a.5.5 0 01.5-.5H2V4z" fill="currentColor"/>
            </svg>
            Kopieren
          </button>
        </div>
        <pre>${escapeHtml(exportMarkdown)}</pre>
      </div>

      <div class="status-message" data-variant="${escapeAttribute(appState.status.variant)}">
        ${escapeHtml(appState.status.message)}
      </div>

      <div class="completion-actions">
        <button type="button" class="button button--ghost" id="summary-back-button">
          <span class="button__icon" aria-hidden="true">&larr;</span>
          <span class="button__label">Zurück</span>
        </button>
        <button type="button" class="button button--icon" id="download-button" title="Markdown exportieren" aria-label="Markdown exportieren">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M8 11.5L3.5 7H6.5V2H9.5V7H12.5L8 11.5Z"/>
            <rect x="2" y="13" width="12" height="1.5" rx="0.75"/>
          </svg>
        </button>
        <button type="button" class="button button--primary-alt" id="restart-button">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Neuer Bericht
        </button>
        <button type="button" class="button button--primary" id="save-button" ${alreadySaved ? "disabled" : ""}>
          ${alreadySaved ? "Bereits gespeichert" : "Speichern"}
        </button>
      </div>
    </article>
  `;

  document.querySelector("#summary-back-button").addEventListener("click", () => {
    clearSaveFeedback();
    appState.mode = "chat";
    if (appState.completionOrigin === "saved-entries") {
      appState.completionOrigin = "chat";
      // Navigate back to the entries tab
      appNav.querySelectorAll(".app-nav__tab").forEach((t) => t.classList.remove("app-nav__tab--active"));
      appNav.querySelector("[data-tab='entries']").classList.add("app-nav__tab--active");
      tabChat.hidden = true;
      tabEntries.hidden = false;
      renderSavedEntries();
    } else {
      appState.completionOrigin = "chat";
      render();
    }
  });

  document.querySelector("#copy-button").addEventListener("click", async (event) => {
    copyWithFeedback(event.currentTarget, exportMarkdown);
  });

  document.querySelector("#download-button").addEventListener("click", () => {
    downloadMarkdown(exportMarkdown);
    setStatus("Markdown exportiert.");
    render();
  });

  document.querySelector("#save-button").addEventListener("click", async () => {
    await saveCurrentReport(signature, exportMarkdown);
    render();
  });

  document.querySelector("#restart-button").addEventListener("click", async () => {
    if (appState.partialEntryId) {
      try { await removeSavedEntry(appState.partialEntryId); appState.savedEntries = appState.savedEntries.filter((e) => e.id !== appState.partialEntryId); } catch (_) {}
    }
    appState.mode = "chat";
    appState.chatMessages = [];
    appState.chatLoading = false;
    appState.chatStreamingText = "";
    appState.collectedFields = {};
    appState.auditNote = "";
    appState.partialEntryId = null;
    appState._restoredFromSession = false;
    appState.values = buildInitialValues();
    appState.otherDetails = {};
    clearSaveFeedback();
    clearSession();
    render();
  });
}

async function saveCurrentReport(signature, exportMarkdown) {
  const exists = appState.savedEntries.some((entry) => entry.signature === signature);

  if (exists) {
    appState.lastSavedSignature = signature;
    setStatus("Dieser Bericht ist bereits gespeichert.", "error");
    return;
  }

  const summary = buildNormalizedSummary();
  const entryPayload = {
    signature,
    name: summary.berichtsname || "Unbenannter Bericht",
    fachabteilung: summary.fachabteilung || "-",
    timestamp: new Date().toLocaleString("de-DE"),
    exportMarkdown,
    summary,
  };

  try {
    const savedEntry = await createSavedEntry(entryPayload);
    appState.savedEntries.unshift(savedEntry);
    appState.savedEntriesError = "";
    appState.lastSavedSignature = signature;
    setStatus("Bericht gespeichert.");
    // Clean up partial entry if it still exists
    if (appState.partialEntryId) {
      const oldId = appState.partialEntryId;
      appState.partialEntryId = null;
      appState.savedEntries = appState.savedEntries.filter((e) => e.id !== oldId);
      removeSavedEntry(oldId).catch(() => {});
    }
  } catch (error) {
    if (error.status === 409) {
      appState.lastSavedSignature = signature;
      setStatus("Dieser Bericht ist bereits gespeichert.", "error");
      return;
    }

    setStatus("Bericht konnte nicht gespeichert werden.", "error");
  }
}

function downloadMarkdown(markdown, berichtsname) {
  const name = berichtsname || buildNormalizedSummary().berichtsname || "berichtskatalog";
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const nameSlug = name
    .toLowerCase()
    .replaceAll(/[^a-z0-9äöüß]+/gi, "-")
    .replaceAll(/^-+|-+$/g, "") || "berichtskatalog";
  const blob = new Blob(["﻿" + markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${yyyy}-${mm}_${dd}_${nameSlug}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function buildNormalizedSummary() {
  const visibleKeys = new Set(getVisibleFields().map((field) => field.key));
  const summary = {};
  const remarkLines = [];

  fieldDefinitions.forEach((field) => {
    let value = appState.values[field.key];

    if (!visibleKeys.has(field.key) && field.defaultValue) {
      value = field.defaultValue;
    }

    if (!value) {
      value = field.defaultValue ?? "";
    }

    if (value === "Sonstiges" && appState.otherDetails[field.key]) {
      remarkLines.push(`${field.exportLabel}: ${appState.otherDetails[field.key]}`);
    }

    summary[field.key] = value;
  });

  const currentRemarks =
    summary.bemerkungen && summary.bemerkungen !== "-" ? [summary.bemerkungen] : [];
  const mergedRemarks = [...currentRemarks, ...remarkLines].filter(Boolean);
  summary.bemerkungen = mergedRemarks.length ? mergedRemarks.join(" | ") : "-";

  return summary;
}

function buildExportMarkdown() {
  const summary = buildNormalizedSummary();
  return [
    "# Berichtskatalog-Eintrag",
    "",
    ...fieldDefinitions.map((field) => `- **${field.exportLabel}:** ${summary[field.key]}`),
  ].join("\n");
}

function renderLiveSummary() {
  const summary = buildNormalizedSummary();
  const highlightedKeys = [
    "berichtsname",
    "berichtstyp",
    "besitzer",
    "fachabteilung",
    "primaereDatenquelle",
    "aktuellesTool",
    "prioritaet",
  ];

  liveSummary.innerHTML = highlightedKeys
    .map((key) => {
      const field = fieldDefinitions.find((entry) => entry.key === key);
      return `
        <dl class="summary-row">
          <dt>${escapeHtml(field.exportLabel)}</dt>
          <dd>${escapeHtml(summary[key] || "-")}</dd>
        </dl>
      `;
    })
    .join("");
}

function renderSavedEntries() {
  if (!appState.savedEntriesLoaded) {
    savedEntriesContainer.innerHTML = `
      <div class="empty-state">
        Gespeicherte Berichte werden geladen.
      </div>
    `;
    return;
  }

  if (appState.savedEntriesError) {
    savedEntriesContainer.innerHTML = `
      <div class="empty-state">
        ${escapeHtml(appState.savedEntriesError)}
      </div>
    `;
    return;
  }

  if (!appState.savedEntries.length) {
    savedEntriesContainer.innerHTML = `
      <div class="empty-state">
        Noch keine gespeicherten Berichte.
      </div>
    `;
    return;
  }

  savedEntriesContainer.innerHTML = appState.savedEntries
    .map((entry) => {
      const isPartial = !entry.complete;
      return `
        <article class="saved-entry${isPartial ? " saved-entry--partial" : ""}">
          <p class="saved-entry__title">
            ${isPartial ? '<span class="saved-entry__badge">Laufend</span>' : ""}
            ${escapeHtml(entry.name)}
          </p>
          <p class="saved-entry__meta">${escapeHtml(entry.fachabteilung)} • ${escapeHtml(entry.timestamp)}</p>
          <div class="saved-entry__actions">
            ${isPartial
              ? `<button class="link-button link-button--primary" type="button" data-resume-id="${escapeAttribute(entry.id)}">Weiterführen</button>`
              : `<button class="link-button" type="button" data-open-id="${escapeAttribute(entry.id)}">Öffnen</button>`
            }
            <button class="link-button" type="button" data-copy-id="${escapeAttribute(entry.id)}">
              Kopieren
            </button>
            <button class="link-button" type="button" data-download-id="${escapeAttribute(entry.id)}">
              Exportieren
            </button>
            <button class="link-button" type="button" data-delete-id="${escapeAttribute(entry.id)}">
              Löschen
            </button>
          </div>
        </article>
      `;
    })
    .join("");

  const entryById = new Map(appState.savedEntries.map((e) => [e.id, e]));

  savedEntriesContainer.querySelectorAll("[data-open-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const entry = entryById.get(button.dataset.openId);
      if (!entry || !entry.summary) {
        return;
      }
      appState.values = { ...buildInitialValues(), ...entry.summary };
      appState.collectedFields = entry.summary || {};
      appState.otherDetails = {};
      appState.mode = "complete";
      appState.completionOrigin = "saved-entries";
      clearSaveFeedback();
      // Switch to Erfassung tab
      appNav.querySelectorAll(".app-nav__tab").forEach((t) => t.classList.remove("app-nav__tab--active"));
      appNav.querySelector("[data-tab='chat']").classList.add("app-nav__tab--active");
      tabChat.hidden = false;
      tabEntries.hidden = true;
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  savedEntriesContainer.querySelectorAll("[data-resume-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const entry = entryById.get(button.dataset.resumeId);
      if (!entry) return;
      appState.chatMessages = Array.isArray(entry.chatMessages) ? entry.chatMessages : [];
      appState.collectedFields = entry.summary || {};
      appState.auditNote = entry.auditNote || "";
      appState.partialEntryId = entry.id;
      appState._restoredFromSession = true;
      appState.values = { ...buildInitialValues(), ...appState.collectedFields };
      appState.mode = "chat";
      appState.chatLoading = false;
      appState.chatStreamingText = "";
      clearSaveFeedback();
      saveSession();
      // Switch to Erfassung tab
      appNav.querySelectorAll(".app-nav__tab").forEach((t) => t.classList.remove("app-nav__tab--active"));
      appNav.querySelector("[data-tab='chat']").classList.add("app-nav__tab--active");
      tabChat.hidden = false;
      tabEntries.hidden = true;
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  savedEntriesContainer.querySelectorAll("[data-copy-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const entry = entryById.get(button.dataset.copyId);
      if (!entry) {
        return;
      }
      copyWithFeedback(button, entry.exportMarkdown);
    });
  });

  savedEntriesContainer.querySelectorAll("[data-download-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const entry = entryById.get(button.dataset.downloadId);
      if (!entry) {
        return;
      }
      downloadMarkdown(entry.exportMarkdown, entry.name);
    });
  });

  savedEntriesContainer.querySelectorAll("[data-delete-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const reportId = button.dataset.deleteId;
      if (!reportId) {
        return;
      }
      if (!window.confirm("Bericht wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.")) {
        return;
      }
      try {
        await removeSavedEntry(reportId);
        appState.savedEntries = appState.savedEntries.filter((item) => item.id !== reportId);
        if (!appState.savedEntries.some((item) => item.signature === appState.lastSavedSignature)) {
          appState.lastSavedSignature = "";
        }
        renderSavedEntries();
      } catch (error) {
        button.textContent = "Fehler";
        window.setTimeout(() => {
          button.textContent = "Löschen";
        }, 1400);
      }
    });
  });
}

function setStatus(message, variant = "success") {
  appState.status = { message, variant };
}

function clearSaveFeedback() {
  appState.status = { message: "", variant: "success" };
  appState.lastSavedSignature = "";
}

function autoResizeTextarea(el) {
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
}

async function copyWithFeedback(btn, text) {
  const original = btn.innerHTML;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "Kopiert ✓";
  } catch {
    btn.textContent = "Fehler";
  }
  window.setTimeout(() => {
    btn.innerHTML = original;
  }, 1400);
}

// ---------------------------------------------------------------------------
// Session persistence (localStorage)
// ---------------------------------------------------------------------------

const SESSION_KEY = "berichtskatalog-session";

function saveSession() {
  try {
    const data = {
      chatMessages: appState.chatMessages,
      collectedFields: appState.collectedFields,
      auditNote: appState.auditNote,
      partialEntryId: appState.partialEntryId,
    };
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(data));
  } catch (_) {}
}

function clearSession() {
  try { window.localStorage.removeItem(SESSION_KEY); } catch (_) {}
}

function tryRestoreSession() {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (!Array.isArray(data.chatMessages) || data.chatMessages.length === 0) return;
    appState.chatMessages = data.chatMessages;
    appState.collectedFields = data.collectedFields || {};
    appState.auditNote = data.auditNote || "";
    appState.partialEntryId = data.partialEntryId || null;
    appState.values = { ...buildInitialValues(), ...appState.collectedFields };
    appState._restoredFromSession = true;
  } catch (_) {
    clearSession();
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

