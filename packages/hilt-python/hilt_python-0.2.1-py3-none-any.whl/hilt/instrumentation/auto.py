"""Auto-instrumentation for HILT - Zero friction LLM observability."""

from typing import Optional, List, Dict, Union
from pathlib import Path

from hilt.io.session import Session
from hilt.instrumentation.context import get_context
from hilt.instrumentation.openai_instrumentor import instrument_openai, uninstrument_openai


def instrument(
    # Backend selection
    backend: Optional[str] = None,
    # Local backend
    filepath: Optional[Union[str, Path]] = None,
    # Google Sheets backend
    sheet_id: Optional[str] = None,
    credentials_path: Optional[str] = None,
    credentials_json: Optional[Dict] = None,
    worksheet_name: str = "Logs",
    # Column filtering - NOW WORKS FOR BOTH BACKENDS!
    columns: Optional[List[str]] = None,
    # Providers to instrument
    providers: Optional[List[str]] = None,
) -> Session:
    """
    🚀 Enable automatic LLM observability with HILT.
    
    After calling this function once, all OpenAI chat completion calls are
    automatically logged without any code changes.
    
    Args:
        backend: Backend type - "local" (JSONL) or "sheets" (Google Sheets)
        
        Local backend:
            filepath: Path to .jsonl file (e.g., "logs/chat.jsonl")
        
        Google Sheets backend:
            sheet_id: Google Sheet ID from URL
            credentials_path: Path to service account credentials JSON
            credentials_json: Credentials as dict (alternative to file)
            worksheet_name: Worksheet name (default: "Logs")
        
        columns: List of columns to log (WORKS FOR BOTH BACKENDS!)
            Available: timestamp, conversation_id, event_id, reply_to, 
            status_code, session, speaker, action, message, tokens_in, 
            tokens_out, cost_usd, latency_ms, model, relevance_score
            
            Example - exclude message content:
                columns=['timestamp', 'speaker', 'action', 'cost_usd', 'model']
        
        providers: List of providers to instrument (default: ["openai"])
            Options: "openai"
    
    Returns:
        Session object (can be used with context manager if needed)
    
    Examples:
        >>> # Option 1: Local JSONL with full events
        >>> from hilt import instrument
        >>> instrument(backend="local", filepath="logs/chat.jsonl")
        
        >>> # Option 2: Local JSONL WITHOUT message content (privacy!)
        >>> instrument(
        ...     backend="local",
        ...     filepath="logs/chat.jsonl",
        ...     columns=['timestamp', 'speaker', 'action', 'cost_usd', 'model']
        ... )
        >>> # ✅ Messages NOT logged to file!
        
        >>> # Option 3: Google Sheets with custom columns
        >>> instrument(
        ...     backend="sheets",
        ...     sheet_id="1abc-xyz",
        ...     credentials_path="credentials.json",
        ...     columns=['timestamp', 'message', 'cost_usd', 'status_code']
        ... )
    
    Notes:
        - Call once at app startup
        - Thread-safe (works with FastAPI, Flask, etc.)
        - Zero performance overhead when not logging
        - Use uninstrument() to disable
    """
    
    # Validate backend
    if backend is None:
        if filepath:
            backend = "local"
        elif sheet_id:
            backend = "sheets"
        else:
            raise ValueError(
                "Must specify either backend='local' with filepath "
                "or backend='sheets' with sheet_id"
            )
    
    # Default providers
    if providers is None:
        providers = ["openai"]
    
    # Create session based on backend
    if backend == "local":
        if filepath is None:
            filepath = "logs/hilt.jsonl"
        
        session = Session(
            backend="local",
            filepath=filepath,
            mode="a",
            create_dirs=True,
            columns=columns  # ← FIX: Maintenant passé au Session!
        )
        print(f"✅ HILT instrumentation enabled")
        print(f"   Backend: Local JSONL")
        print(f"   File: {filepath}")
        if columns:
            print(f"   Columns: {len(columns)} selected (message {'excluded' if 'message' not in columns else 'included'})")
        else:
            print(f"   Columns: All (full events)")
    
    elif backend == "sheets":
        session = Session(
            backend="sheets",
            sheet_id=sheet_id,
            credentials_path=credentials_path,
            credentials_json=credentials_json,
            worksheet_name=worksheet_name,
            columns=columns
        )
        print(f"✅ HILT instrumentation enabled")
        print(f"   Backend: Google Sheets")
        print(f"   Sheet ID: {sheet_id}")
        print(f"   Worksheet: {worksheet_name}")
        if columns:
            print(f"   Columns: {len(columns)} selected (message {'excluded' if 'message' not in columns else 'included'})")
    
    else:
        raise ValueError(f"Invalid backend: {backend}. Must be 'local' or 'sheets'")
    
    # Open session (it will stay open for the app lifetime)
    session.open()
    
    # Set global session in context
    context = get_context()
    context.set_global_session(session)
    
    # Instrument providers
    print(f"   Providers: {', '.join(providers)}")
    
    if "openai" in providers:
        instrument_openai()
    
    return session


def uninstrument():
    """
    Disable HILT instrumentation.
    
    Removes all monkey-patching and closes the session.
    
    Example:
        >>> from hilt import uninstrument
        >>> uninstrument()
        >>> # LLM calls are no longer logged
    """
    context = get_context()
    
    # Close session if exists
    if context.session:
        try:
            context.session.close()
        except:
            pass
    
    # Clear context
    context.clear()
    
    # Uninstrument providers
    uninstrument_openai()
    
    print("🔓 HILT instrumentation disabled")


__all__ = ['instrument', 'uninstrument']