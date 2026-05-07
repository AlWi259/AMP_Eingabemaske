const THEME_KEY = "berichtskatalog-theme";
const API_BASE_URL =
  window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : `${window.location.origin}/api`;

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
    required: false,
    defaultValue: "-",
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
    required: false,
    defaultValue: "Unbekannt",
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
const liveSummary = document.querySelector("#live-summary");
const savedEntriesContainer = document.querySelector("#saved-entries");
const themeToggle = document.querySelector("#theme-toggle");

const appState = {
  currentIndex: 0,
  values: buildInitialValues(),
  otherDetails: {},
  savedEntries: [],
  savedEntriesLoaded: false,
  savedEntriesError: "",
  theme: loadTheme(),
  status: { message: "", variant: "success" },
  lastSavedSignature: "",
};

applyTheme(appState.theme);
themeToggle.addEventListener("click", toggleTheme);
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
  // Keep the switch state in sync with the active theme.
  themeToggle.setAttribute("aria-checked", String(theme === "dark"));
}

function toggleTheme() {
  appState.theme = appState.theme === "dark" ? "light" : "dark";
  try {
    window.localStorage.setItem(THEME_KEY, appState.theme);
  } catch (error) {
    // The theme still changes even if the browser blocks storage.
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

function getCurrentField() {
  return getVisibleFields()[appState.currentIndex] ?? null;
}

function render() {
  renderAssistantContent();
  renderLiveSummary();
  renderSavedEntries();
}

function renderAssistantContent() {
  const currentField = getCurrentField();

  if (!currentField) {
    renderCompletion();
    return;
  }

  const visibleFields = getVisibleFields();
  const progress = Math.round((appState.currentIndex / visibleFields.length) * 100);

  assistantContent.innerHTML = `
    <div class="assistant-card__header">
      <h2>${escapeHtml(currentField.label)}</h2>
      <div class="progress-box">
        <div class="progress-box__label">
          <span>Schritt ${appState.currentIndex + 1} von ${visibleFields.length}</span>
          <span>${progress}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-bar__fill" style="width: ${progress}%"></div>
        </div>
      </div>
    </div>

    <div class="category-line">${escapeHtml(currentField.category)}</div>

    <form id="assistant-form" novalidate>
      <div class="question-card">
        <div class="question-card__meta">
          <span class="question-card__index">${String(appState.currentIndex + 1).padStart(2, "0")}</span>
          <span class="question-card__required ${currentField.required ? "" : "question-card__required--hidden"}">Pflichtfeld</span>
        </div>

        <label class="question-card__label" for="field-input">
          ${escapeHtml(currentField.label)}
        </label>

        ${buildFieldMarkup(currentField)}

        <div class="question-card__notice" id="field-notice"></div>
      </div>

      <div class="actions">
        <button type="button" class="button button--ghost" id="back-button" ${appState.currentIndex === 0 ? "disabled" : ""}>
          <span class="button__icon" aria-hidden="true">&larr;</span>
          <span class="button__label">Zurück</span>
        </button>
        <div class="actions__group">
          ${currentField.required ? "" : '<button type="button" class="button button--subtle" id="skip-button"><span class="button__icon" aria-hidden="true">&raquo;</span><span class="button__label">Überspringen</span></button>'}
          <button type="submit" class="button button--primary">
            ${appState.currentIndex === visibleFields.length - 1 ? "Zur Zusammenfassung" : "Weiter"}
          </button>
        </div>
      </div>
    </form>
  `;

  const form = document.querySelector("#assistant-form");
  const backButton = document.querySelector("#back-button");
  const skipButton = document.querySelector("#skip-button");
  const fieldInput = document.querySelector("#field-input");

  form.addEventListener("submit", handleSubmit);
  backButton.addEventListener("click", handleBack);

  if (skipButton) {
    skipButton.addEventListener("click", handleSkip);
  }

  if (currentField.type === "select" && fieldInput) {
    fieldInput.addEventListener("change", handleSelectChange);
  }

  const textarea = assistantContent.querySelector("textarea");
  if (textarea) {
    autoResizeTextarea(textarea);
    textarea.addEventListener("input", () => autoResizeTextarea(textarea));
  }

  if (fieldInput) {
    fieldInput.focus();
  }
}

function buildFieldMarkup(field) {
  const value = appState.values[field.key] ?? "";
  const displayValue = value === field.defaultValue ? "" : value;

  if (field.type === "textarea") {
    return `
      <div class="field-control">
        <textarea id="field-input" rows="1" placeholder="${escapeAttribute(field.placeholder ?? "")}">${escapeHtml(displayValue)}</textarea>
      </div>
    `;
  }

  if (field.type === "select") {
    const options = field.options
      .map((option) => {
        const selected = option === value ? "selected" : "";
        return `<option value="${escapeAttribute(option)}" ${selected}>${escapeHtml(option)}</option>`;
      })
      .join("");

    const showOther = value === "Sonstiges";
    const otherValue = appState.otherDetails[field.key] ?? "";

    return `
      <div class="field-grid">
        <div class="field-control select-wrap">
          <select id="field-input">
            <option value="">Bitte auswählen</option>
            ${options}
          </select>
        </div>
        <div class="field-control" id="other-field" ${showOther ? "" : "hidden"}>
          <input
            type="text"
            id="other-input"
            value="${escapeAttribute(otherValue)}"
            placeholder="Sonstiges"
          />
        </div>
      </div>
    `;
  }

  if (field.type === "number") {
    return `
      <div class="field-control">
        <input
          type="number"
          id="field-input"
          min="0"
          step="0.5"
          value="${escapeAttribute(displayValue === "-" ? "" : displayValue)}"
          placeholder="${escapeAttribute(field.placeholder ?? "")}"
        />
      </div>
    `;
  }

  return `
    <div class="field-control">
      <input
        type="text"
        id="field-input"
        value="${escapeAttribute(displayValue)}"
        placeholder="${escapeAttribute(field.placeholder ?? "")}"
      />
    </div>
  `;
}

function handleSelectChange(event) {
  const currentField = getCurrentField();
  if (!currentField) {
    return;
  }

  const isOther = event.target.value === "Sonstiges";
  const otherField = document.querySelector("#other-field");

  if (otherField) {
    otherField.hidden = !isOther;
  }

  if (!isOther) {
    delete appState.otherDetails[currentField.key];
  }
}

function handleSubmit(event) {
  event.preventDefault();

  const currentField = getCurrentField();
  if (!currentField) {
    return;
  }

  const payload = readFieldValue();
  const validation = validateField(currentField, payload.value, payload.otherValue);
  const notice = document.querySelector("#field-notice");

  if (!validation.valid) {
    notice.textContent = validation.message;
    return;
  }

  notice.textContent = "";
  appState.values[currentField.key] = validation.value;

  if (validation.otherValue) {
    appState.otherDetails[currentField.key] = validation.otherValue;
  } else {
    delete appState.otherDetails[currentField.key];
  }

  if (currentField.key === "manuellerAufwand" && validation.value === "Kein Aufwand") {
    appState.values.aufwandKonkret = "-";
  }

  clearSaveFeedback();

  const visibleFields = getVisibleFields();
  appState.currentIndex =
    appState.currentIndex >= visibleFields.length - 1
      ? visibleFields.length
      : appState.currentIndex + 1;

  render();
}

function handleBack() {
  if (appState.currentIndex === 0) {
    return;
  }

  clearSaveFeedback();
  appState.currentIndex -= 1;
  render();
}

function handleSkip() {
  const currentField = getCurrentField();
  if (!currentField || currentField.required) {
    return;
  }

  appState.values[currentField.key] = currentField.defaultValue ?? "-";
  delete appState.otherDetails[currentField.key];
  clearSaveFeedback();
  appState.currentIndex += 1;
  render();
}

function readFieldValue() {
  const mainInput = document.querySelector("#field-input");
  const otherInput = document.querySelector("#other-input");

  return {
    value: mainInput ? mainInput.value.trim() : "",
    otherValue: otherInput ? otherInput.value.trim() : "",
  };
}

function validateField(field, rawValue, otherValue) {
  if (!rawValue) {
    if (field.required) {
      return { valid: false, message: "Bitte dieses Feld ausfüllen." };
    }

    return { valid: true, value: field.defaultValue ?? "-", otherValue: "" };
  }

  if (field.type === "number") {
    const parsed = Number(rawValue);
    if (Number.isNaN(parsed) || parsed < 0) {
      return {
        valid: false,
        message: "Bitte einen sinnvollen Aufwand in Personentagen angeben.",
      };
    }

    return { valid: true, value: String(parsed), otherValue: "" };
  }

  if (field.type === "monthText" && !/^(0[1-9]|1[0-2])\.\d{4}$/.test(rawValue)) {
    return {
      valid: false,
      message: "Bitte im Format MM.JJJJ eingeben, zum Beispiel 03.2025.",
    };
  }

  if (field.type === "select" && rawValue === "Sonstiges" && !otherValue) {
    return {
      valid: false,
      message: "Bitte den Sonstiges-Wert ergänzen.",
    };
  }

  return {
    valid: true,
    value: rawValue,
    otherValue: rawValue === "Sonstiges" ? otherValue : "",
  };
}

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
        <button type="button" class="button button--icon button--primary-alt" id="restart-button" title="Neuer Bericht" aria-label="Neuer Bericht">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M9 1H3.5A1.5 1.5 0 002 2.5v11A1.5 1.5 0 003.5 15h9A1.5 1.5 0 0014 13.5V6l-5-5z"/>
            <path d="M9 1v5h5" fill="none" stroke="white" stroke-width="1.2"/>
            <path d="M8 9v4M6 11h4" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
        <button type="button" class="button button--primary" id="save-button" ${alreadySaved ? "disabled" : ""}>
          ${alreadySaved ? "Bereits gespeichert" : "Speichern"}
        </button>
      </div>
    </article>
  `;

  document.querySelector("#summary-back-button").addEventListener("click", () => {
    clearSaveFeedback();
    appState.currentIndex = Math.max(getVisibleFields().length - 1, 0);
    render();
  });

  document.querySelector("#copy-button").addEventListener("click", async (event) => {
    const btn = event.currentTarget;
    try {
      await navigator.clipboard.writeText(exportMarkdown);
      btn.textContent = "Kopiert ✓";
    } catch (error) {
      btn.textContent = "Fehler";
    }
    window.setTimeout(() => {
      btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect x="4.5" y="0.5" width="10" height="10" rx="1.5" stroke="currentColor"/><path d="M2 4H1.5A1.5 1.5 0 000 5.5v8A1.5 1.5 0 001.5 15h8A1.5 1.5 0 0011 13.5V13H9.5v.5a.5.5 0 01-.5.5h-8a.5.5 0 01-.5-.5v-8a.5.5 0 01.5-.5H2V4z" fill="currentColor"/></svg> Kopieren`;
    }, 1600);
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

  document.querySelector("#restart-button").addEventListener("click", () => {
    appState.currentIndex = 0;
    appState.values = buildInitialValues();
    appState.otherDetails = {};
    clearSaveFeedback();
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
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
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
      return `
        <article class="saved-entry">
          <p class="saved-entry__title">${escapeHtml(entry.name)}</p>
          <p class="saved-entry__meta">${escapeHtml(entry.fachabteilung)} • ${escapeHtml(entry.timestamp)}</p>
          <div class="saved-entry__actions">
            <button class="link-button" type="button" data-open-id="${escapeAttribute(entry.id)}">
              Öffnen
            </button>
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

  savedEntriesContainer.querySelectorAll("[data-open-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const entry = appState.savedEntries.find((item) => item.id === button.dataset.openId);
      if (!entry || !entry.summary) {
        return;
      }
      appState.values = { ...buildInitialValues(), ...entry.summary };
      appState.otherDetails = {};
      appState.currentIndex = 0;
      clearSaveFeedback();
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  savedEntriesContainer.querySelectorAll("[data-copy-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const entry = appState.savedEntries.find((item) => item.id === button.dataset.copyId);
      if (!entry) {
        return;
      }

      try {
        await navigator.clipboard.writeText(entry.exportMarkdown);
        button.textContent = "Kopiert";
      } catch (error) {
        button.textContent = "Fehler";
      }

      window.setTimeout(() => {
        button.textContent = "Kopieren";
      }, 1400);
    });
  });

  savedEntriesContainer.querySelectorAll("[data-download-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const entry = appState.savedEntries.find((item) => item.id === button.dataset.downloadId);
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
