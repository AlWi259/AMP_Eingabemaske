# Azure Ressourcen Übersicht – Yggdrasil Chatbot

> Zweck: Ressourcen-Delta zwischen Kunden-Tenant und eigenem Tenant identifizieren.  
> Quellen: `azure-pipelines.yml`, `services/az_functions/`, `services/streamlit/`

---

## 1. Container Registry

| Name | Login Server | Subscription | Resource Group |
|---|---|---|---|
| `acryggdrasil` | `acryggdrasil.azurecr.io` | `sc-advia-ygg` | `rg-yggdrasil-test` |

**Verwendung:** Docker-Images für das Streamlit-Frontend (`yggdrasil-frontend`)

---

## 2. Azure Function Apps

Für das Interview wird **nur eine einzige Function App** benötigt. Die anderen drei sind in der `azure-pipelines.yml` als Variablen definiert, existieren aber nicht als Code im Repository und werden vom Interview nicht aufgerufen.

### `func-yggdrasil-llm` ✅ NOTWENDIG

Alle Interview-Endpoints laufen über diese eine Function App:

| Endpoint | Zweck |
|---|---|
| `/api/interview_agent` | Hauptendpoint – verarbeitet User-Antworten, generiert nächste Frage |
| `/api/interview_status` | Lädt aktuellen Interview-Status und Chat-Verlauf |
| `/api/generate_final_summary` | Generiert finale Zusammenfassung |
| `/api/save_final_summary` | Speichert bearbeitete Zusammenfassung |
| `/api/delete_interview_history` | Löscht Interview-Verlauf |

**App Service Plan:** Linux, Service Connection `sc-yggdrasil-test`

### Nicht notwendig für das Interview

| Name | Status |
|---|---|
| `func-yggdrasil-retrieval` | Kein Code vorhanden, Graphiti-Feature (nicht Interview) |
| `func-yggdrasil-embedding` | Kein Code vorhanden |
| `func-yggdrasil-transcription` | Kein Code vorhanden, altes Audio-Feature |

---

## 3. Storage Account

### Produktiv-Storage: `styggdrasil`

| Typ | Name | Inhalt |
|---|---|---|
| Blob Container | `audio-raw` | Rohe Audio-Dateien |
| Blob Container | `yggs-summarized` | Verarbeitete YGG-Zusammenfassungen |
| Blob Container | `interview-yggs-demo` | Haupt-Datenspeicher für LLM-Functions |
| Table | `interviewstatesdemo` | Status je Interview & User |
| Table | `interviewmessagesdemo` | Chat-Verlauf |
| Table | `interviewanswers` | Gespeicherte Antwort-Zusammenfassungen |
| Table | `jobstatus` | Verarbeitungsstatus für Audio-Jobs |

**Blob-Struktur in `interview-yggs-demo`:**
```
temporary-data/
  topic-summaries/{interview_id}-{chat_id}-topic_summaries.json
  message-history/{interview_id}-{chat_id}-messages.json
  final-summaries/{interview_id}-{user_id}-final_summary.json
saved-data/
  topic-summaries/...
  message-history/...
  final-summaries/...
```

> Dev-Storage `staygg` ist nur für lokale Entwicklung relevant, wird für Production-Deployment nicht benötigt.

---

## 4. Key Vault

| Name | URL |
|---|---|
| `kv-yggdrasil-test01` | `https://kv-yggdrasil-test01.vault.azure.net/` |

**Gespeicherte Secrets:**

| Secret Name | Inhalt |
|---|---|
| `openai-api-url` | Azure OpenAI Endpoint URL |
| `openai-api-key` | Azure OpenAI API Key |
| `embedding-api-url` | Azure OpenAI Embedding Endpoint URL |
| `embedding-api-key` | Azure OpenAI Embedding API Key |

---

## 5. Azure AI Foundry / Azure OpenAI

**Endpoint:** `aif-yggdrasil.cognitiveservices.azure.com`

| Deployment Name | Modell | API Version | Verwendung |
|---|---|---|---|
| `gpt-4.1` | GPT-4.1 | `2024-12-01-preview` | Haupt-LLM für Interview-Agent |
| `gpt-4o` | GPT-4o | `2024-12-01-preview` | Graphiti Knowledge Graph |
| `embedding-ada-yggdrasil` | text-embedding-ada-002 | `2023-05-15` | Embedding-Verarbeitung |

---

## 6. Application Insights / Log Analytics

Wird automatisch mit den Azure Function Apps erstellt (konfiguriert in `host.json`).  
Explizit kein eigener Name referenziert – wird beim Anlegen der Function Apps miterstellt.

---

## 7. Service Connections (Azure DevOps)

| Name | Verwendung |
|---|---|
| `sc-advia-ygg` | Container Registry + Function App Deployments |
| `sc-yggdrasil-test` | Azure Functions Service Connection (in Pipeline-Variablen) |
| `sc-docker-registry-yggdrasil-test` | Docker Registry (in Pipeline-Variablen) |

---

## 8. Vollständige Ressourcen-Checkliste (für Delta-Vergleich)

Nutze diese Liste um zu prüfen, was auf dem eigenen Tenant noch fehlt:

- [ ] **Azure Container Registry** `acryggdrasil`
- [ ] **Azure Function App** `func-yggdrasil-llm` *(einzige notwendige Function App)*
- [ ] **App Service Plan** (Linux)
- [ ] **Storage Account** `styggdrasil` inkl. Blob Container + Tables (siehe oben)
- [ ] **Key Vault** `kv-yggdrasil-test01` inkl. der 4 Secrets
- [ ] **Azure OpenAI Resource** `aif-yggdrasil`
  - [ ] Deployment `gpt-4.1`
  - [ ] Deployment `gpt-4o`
  - [ ] Deployment `embedding-ada-yggdrasil`
- [ ] **Application Insights** (wird mit Function Apps erstellt)
- [ ] **Service Connection** `sc-advia-ygg` in Azure DevOps
- [ ] **Service Connection** `sc-yggdrasil-test` in Azure DevOps
- [ ] **Service Connection** `sc-docker-registry-yggdrasil-test` in Azure DevOps
- [ ] **Resource Group** `YGG`

---

## 9. Hinweise / Offene Punkte

- **Graphiti/Neo4j:** Die `graphiti_client.py` referenziert eine Neo4j-Verbindung (`bolt://localhost:7687`). In Production muss geklärt werden, ob dafür eine eigene VM/Container oder ein Managed Neo4j-Service läuft – das ist aktuell nicht in der Pipeline sichtbar.
- **Langfuse:** Externes LLM-Observability-Tool, kein Azure-Dienst. Keys sind in `local.settings.json` hinterlegt – für Production müssen diese in den Key Vault oder die Function App Settings.
- **Streamlit Frontend:** Läuft als Docker Container über die Container Registry. Benötigt zusätzlich einen **Azure Container Apps** oder **Azure App Service** zum Hosten – dieser ist in der Pipeline nicht explizit deployt, nur gebaut und gepusht.
