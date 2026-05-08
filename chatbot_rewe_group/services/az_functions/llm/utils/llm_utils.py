
from models.llm.LLMMetadata import LLMMetadata
from typing import Any
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from langchain_openai import AzureChatOpenAI

# Only import logfire in development environment
# If ENVIRONMENT is not set, assume production (no logfire)
try:
    if os.environ.get("ENVIRONMENT", "prod").lower() == "dev":
        import logfire
    else:
        logfire = None
except ImportError:
    # If logfire is not installed, set to None
    logfire = None

def store_token_usage(llm_response: Any, llm_metadata: LLMMetadata) -> LLMMetadata:
    """
    Update the LLMMetadata dictionary with token usage from an LLM response.
    Args:
        llm_response (Any): The LLM response object, expected to have a 'usage_metadata' dict with keys 'output_tokens', 'input_tokens', and 'total_tokens'.
        llm_metadata (LLMMetadata): The metadata dictionary to update.
    Returns:
        LLMMetadata: The updated metadata dictionary.
    Raises:
        KeyError: If required keys are missing in llm_response.usage_metadata or llm_metadata.
    """
    try:
        llm_metadata['completion_tokens'] += llm_response.usage_metadata["output_tokens"]
        llm_metadata["prompt_tokens"] += llm_response.usage_metadata["input_tokens"]
        llm_metadata["total_tokens"] += llm_response.usage_metadata["total_tokens"]
    except Exception as e:
        import logging
        logging.error(f"Failed to update LLMMetadata with token usage: {e}")
        raise
    return llm_metadata

def get_llm(temperature: float = 0.4) -> AzureChatOpenAI:
    """
    Configure and return your LLM instance.
    This is a placeholder function. Replace with actual LLM configuration logic.
    """
    if logfire:
        logfire.configure()

    key_vault_url = os.environ.get("KEY_VAULT_URL", "")
    secrets = get_keyvault_secrets(key_vault_url)
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        api_version="2024-12-01-preview",
        temperature=temperature,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=secrets["openai_key"],
        azure_endpoint=secrets["openai_url"]
    )

    if logfire:
        logfire.instrument_openai()
    return llm

# --- LLM Initialization Helpers ---
def get_keyvault_secrets(key_vault_url: str) -> dict:
    """
    Fetch all required secrets from Azure Key Vault and return as a dict.
    Args:
        key_vault_url (str): The URL of the Azure Key Vault.
    Returns:
        dict: Dictionary containing required secrets for LLM.
    """
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)
    return {
        "openai_url": client.get_secret("openai-api-url").value,
        "openai_key": client.get_secret("openai-api-key").value,
        "embedding_url": client.get_secret("embedding-api-url").value,
        "embedding_api_key": client.get_secret("embedding-api-key").value
    }