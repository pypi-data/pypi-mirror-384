from __future__ import annotations

from leann import LeannBuilder, LeannSearcher, LeannChat
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Dict, Any
from pathlib import Path
import os

from struct_agent.instructor_based import ToolSpec

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("LEANN_CHAT_API_KEY")
os.environ["OPENAI_BASE_URL"] = os.getenv("LEANN_CHAT_BASE_URL")

# Use the project root directory for persistent storage
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_INDEX_DIR = PROJECT_ROOT / "leann_index"

# Handle LEANN_INDEX_PATH from environment variable or use default
leann_index_path_env = os.getenv("LEANN_INDEX_PATH")
if leann_index_path_env:
    # Treat it as an absolute path
    INDEX_DIR = Path(leann_index_path_env)
else:
    INDEX_DIR = DEFAULT_INDEX_DIR

# Construct the full path to the vector index file
INDEX_PATH = INDEX_DIR / "vector.leann"

# Ensure the index directory exists
INDEX_DIR.mkdir(parents=True, exist_ok=True)
BACKEND_NAME = "hnsw"
CHAT_MODEL = os.getenv("LEANN_CHAT_MODEL")

class AddTextArgs(BaseModel):
    """Inputs for the LEANN add text tool."""
    text_content: str = Field(..., description="The text content to add to the index.")

class AddTextResponse(BaseModel):
    """Response from the LEANN add text tool."""
    message: str = Field(..., description="Confirmation message")

class SearchArgs(BaseModel):
    """Inputs for the LEANN search tool."""
    query: str = Field(..., description="The search query to find similar content.")
    top_k: int = Field(5, description="Number of top results to return. Default: 5")

class SearchResponse(BaseModel):
    """Response from the LEANN search tool."""
    results: list = Field(..., description="Search results from the index")

class ChatArgs(BaseModel):
    """Inputs for the LEANN chat tool."""
    query: str = Field(..., description="The question or message to send to the RAG system.")
    top_k: int = Field(5, description="Number of top results to retrieve for context. Default: 5")

class ChatResponse(BaseModel):
    """Response from the LEANN chat tool."""
    response: str = Field(..., description="Chat response from the RAG system")

def make_leann_add_text_tool() -> ToolSpec:
    """Add text content to the LEANN index."""

    def handler(args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parsed_args = AddTextArgs(**args)

            builder = LeannBuilder(backend_name=BACKEND_NAME)
            builder.add_text(parsed_args.text_content)
            builder.build_index(INDEX_PATH)

            return {"message": "Text added to index"}
        except Exception as e:
            return {"error": f"Failed to add text to index: {str(e)}"}

    return ToolSpec(
        name="vector_index_add_text",
        description="Add text content to the LEANN vector index for semantic search and retrieval.",
        args_model=AddTextArgs,
        # response_model=AddTextResponse,
        handler=handler,
        parameters={"text_content": "string content to add to index"},
    )

def make_leann_search_tool() -> ToolSpec:
    """Search the LEANN index for relevant content."""

    def handler(args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parsed_args = SearchArgs(**args)

            searcher = LeannSearcher(INDEX_PATH)
            results = searcher.search(parsed_args.query, top_k=parsed_args.top_k)

            return {"results": results}
        except Exception as e:
            return {"error": f"Failed to search index: {str(e)}"}

    return ToolSpec(
        name="vector_index_search",
        description="Search the LEANN vector index for semantically similar content.",
        args_model=SearchArgs,
        # response_model=SearchResponse,
        handler=handler,
        parameters={"query": "string search query", "top_k": "integer number of results to return"},
    )

def make_leann_chat_tool() -> ToolSpec:
    """Chat with the LEANN index using RAG + LLM."""

    def handler(args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parsed_args = ChatArgs(**args)

            chat = LeannChat(INDEX_PATH, llm_config={"type": "openai", "model": CHAT_MODEL})
            response = chat.ask(parsed_args.query, top_k=parsed_args.top_k)

            return {"response": response}
        except Exception as e:
            return {"error": f"Failed to chat with index: {str(e)}"}

    return ToolSpec(
        name="vector_index_rag_llm_chat",
        description="Chat with the LEANN vector index using RAG (Retrieval-Augmented Generation) + LLM.",
        args_model=ChatArgs,
        handler=handler,
        parameters={"query": "string question or message", "top_k": "integer number of context results"},
    )

__all__ = [
    "make_leann_add_text_tool",
    "make_leann_search_tool",
    "make_leann_chat_tool"
]