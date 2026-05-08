# Interview Assistant - REWE Group

An AI-powered interview assistant built on the YGG-app conversational framework for conducting structured interviews about Microsoft 365 Copilot usage experiences. This showcase application demonstrates intelligent conversation flows with state management using LangGraph and Azure services.

## Overview

This project provides an interactive interview platform where users can share their experiences with Microsoft 365 Copilot. The system uses advanced language models and state management to conduct natural, flowing interviews with intelligent follow-up questions and comprehensive summarization.

## Architecture

### Services

#### Streamlit Frontend (`services/streamlit/`)

- **Technology**: Streamlit
- **Purpose**: User-facing web interface for conducting interviews
- **Key Features**:
  - Multi-page application with navigation
  - Real-time interview transcription
  - Response review and editing capabilities
  - Custom styling with REWE and Advia branding

#### Python Backend (`services/backend/`)

- **Technology**: FastAPI, Uvicorn, LangGraph, LangChain
- **Purpose**: AI-powered conversation management and processing via REST API
- **Components**:
  - `main.py` – FastAPI application with all API endpoints
  - **Shared logic from `az_functions/llm/`** (included via Dockerfile build context):
    - `state_nodes/` – Modular conversation flow nodes (intro, questions, follow-up, summary)
    - `adapters/` – Azure Storage, Table, and Blob clients
    - `models/` – Pydantic data models
    - `utils/` – Helper functions, LLM configuration, file loaders
    - `interview_graph.py` – LangGraph graph definition
    - `prompt_templates/` – Prompt templates

### Key Technologies

- **Frontend**: Streamlit
- **Backend**: FastAPI, LangChain, LangGraph, OpenAI
- **Cloud Services**: Azure Blob Storage, Azure Table Storage, Azure Key Vault
- **AI/ML**: OpenAI models, LangGraph state management
- **Packaging**: uv (dependency management)

## Features

- **Intelligent Conversation Flow**: State-driven interview progression with LangGraph
- **Dynamic Follow-up Questions**: Context-aware follow-up generation based on user responses
- **Response Transcription**: Real-time capture and storage of interview responses
- **Review & Edit**: Users can review and modify their responses before submission
- **Data Visualization**: Analysis capabilities with charts and word clouds
- **Azure Integration**: Secure storage and processing with Azure services
- **Multi-tenant Ready**: Client information tracking for different deployments

## Getting Started

### Prerequisites

- Python 3.12+
- Azure subscription with configured services:
  - Azure Blob Storage
  - Azure Table Storage
  - Azure Key Vault
- Docker (for containerization)

### Local Development

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd chatbot_rewe_group
   ```

2. **Start the backend**

   ```bash
   cd services/backend
   cp .env.example .env
   # Fill in your Azure credentials

   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

   # The shared code from az_functions/llm/ must be available in the working directory.
   # In Docker this happens automatically via the build context.

   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start the frontend**

   ```bash
   cd services/streamlit
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   streamlit run Interview.py
   ```

### Docker Deployment

Backend and frontend are each started via Docker Compose. The backend's build context is `services/` so that the shared code from `az_functions/llm/` is included automatically.

```bash
# Backend
cd services/backend
docker-compose up --build

# Frontend
cd services/streamlit
docker-compose up --build
```

## CI/CD Pipeline

The project uses Azure Pipelines for automated deployment:

- **Trigger Branches**: `development`, `dev`, `dev-rewe`
- **Build Process**:
  - Docker image building via Docker Compose
  - Automated tagging with timestamps and build IDs
  - Push to Azure Container Registry (ACR)
- **Deployment Target**: Azure Container Instances or App Services

See [azure-pipelines.yml](azure-pipelines.yml) for detailed build and deployment steps.

## Project Structure

```
chatbot_rewe_group/
├── services/
│   ├── streamlit/              # Frontend application
│   │   ├── Interview.py        # Main application entry
│   │   ├── pages/              # Multi-page app structure
│   │   ├── adapters/           # Azure service clients
│   │   ├── utils/              # Utility functions
│   │   ├── rendering/          # UI rendering components
│   │   ├── static/             # Images, CSS, assets
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── backend/                # FastAPI backend
│   │   ├── main.py             # FastAPI app & API endpoints
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── az_functions/
│       └── llm/                # Shared business logic (used by the backend)
│           ├── state_nodes/    # LangGraph conversation nodes
│           ├── adapters/       # Azure clients
│           ├── models/         # Pydantic models
│           ├── utils/          # Helper utilities
│           ├── interview_graph.py
│           └── prompt_templates/
├── azure-pipelines.yml         # CI/CD configuration
├── .gitignore
└── README.md
```

## Configuration

### Environment Variables

Required environment variables (configure in `services/backend/.env`):

- **Azure Storage**
  - `AZURE_STORAGE_CONNECTION_STRING`
  - `AZURE_STORAGE_ACCOUNT_NAME`
  - `AZURE_STORAGE_ACCOUNT_KEY`
- **Azure Tables**
  - `AZURE_TABLE_CONNECTION_STRING`
- **Azure Key Vault**
  - `AZURE_KEY_VAULT_URL`
- **OpenAI**
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (optional, defaults configured)

## Usage

1. **Start Interview**: Navigate to the home page and click "Interview starten"
2. **Answer Questions**: Respond to questions about Microsoft 365 Copilot usage
3. **Review Responses**: Check and edit your answers before submission
4. **Submit**: Finalize and submit your interview responses

## Acknowledgments

This project makes use of pattern templates from [fabric](https://github.com/danielmiessler/fabric), licensed under the MIT License.

## Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Contact

For questions or support, please contact the development team.
