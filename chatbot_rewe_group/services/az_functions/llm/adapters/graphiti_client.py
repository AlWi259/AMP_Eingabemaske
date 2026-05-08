import os
os.environ['GRAPHITI_TELEMETRY_ENABLED'] = 'false'

from openai import AsyncAzureOpenAI
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.nodes import EpisodeType
from dotenv import load_dotenv
import json
from datetime import datetime, timezone
from utils.llm_utils import get_keyvault_secrets
from typing import List, Dict

load_dotenv()

def get_graphiti_client() -> Graphiti:
    kv_secrets = get_keyvault_secrets(os.environ.get("KEY_VAULT_URL", ""))
    openai_key = kv_secrets["openai_key"]
    openai_url = kv_secrets["openai_url"]

    os.environ.setdefault("OPENAI_API_KEY", openai_key)
    os.environ.setdefault("OPENAI_API_URL", openai_url)

    embedding_api_key = kv_secrets["embedding_api_key"]
    embedding_endpoint = kv_secrets["embedding_url"]

    llm_api_version = "2024-12-01-preview"
    llm_deployment_name = "gpt-4o"
    embedding_api_version = "2023-05-15"
    embedding_deployment_name = "embedding-ada-yggdrasil"

    neo4j_url = "bolt://localhost:7687"
    neo4j_user = "neo4j"
    neo4j_password = "testpassword"

    llm_client_azure = AsyncAzureOpenAI(
        api_key=openai_key,
        api_version=llm_api_version,
        azure_deployment=llm_deployment_name,
        azure_endpoint=openai_url
    )

    embedding_client_azure = AsyncAzureOpenAI(
        api_key=embedding_api_key,
        azure_endpoint=embedding_endpoint,
        api_version=embedding_api_version,
        azure_deployment=embedding_deployment_name
    )

    azure_llm_config = LLMConfig(
        model=llm_deployment_name
    )

    graphiti = Graphiti(
        neo4j_url,
        neo4j_user,
        neo4j_password,
        llm_client=OpenAIClient(
            client=llm_client_azure,
            config=azure_llm_config
        ),
        embedder=OpenAIEmbedder(
            config=OpenAIEmbedderConfig(
                embedding_model="embedding-ada-yggdrasil"
            ),
            client=embedding_client_azure
        )
    )

    return graphiti

async def add_episodes_to_graph(graphiti: Graphiti, episodes: List[str]) -> None:
    """
    Add episodes to the Graphiti instance.
    This function is asynchronous and should be run in an event loop.
    """
    await graphiti.build_indices_and_constraints()

    # Add episodes to the graph
    for i, episode in enumerate(episodes):
        await graphiti.add_episode(
            name=episode['title'],
            group_id=episode['group_id'],
            episode_body=episode['content'],
            source=EpisodeType.text,
            source_description="general ygg",
            reference_time=datetime.now(timezone.utc),
        )
        print(f'Added episode: Ygg {i}')