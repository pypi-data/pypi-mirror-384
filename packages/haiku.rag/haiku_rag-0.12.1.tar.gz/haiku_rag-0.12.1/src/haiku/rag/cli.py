import asyncio
import json
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import Any

import typer

from haiku.rag.config import Config
from haiku.rag.logging import configure_cli_logging
from haiku.rag.utils import is_up_to_date

cli = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True
)


async def check_version():
    """Check if haiku.rag is up to date and show warning if not."""
    up_to_date, current_version, latest_version = await is_up_to_date()
    if not up_to_date:
        typer.echo(
            f"Warning: haiku.rag is outdated. Current: {current_version}, Latest: {latest_version}",
        )
        typer.echo("Please update.")


def version_callback(value: bool):
    if value:
        v = version("haiku.rag")
        typer.echo(f"haiku.rag version {v}")
        raise typer.Exit()


@cli.callback()
def main(
    _version: bool = typer.Option(
        False,
        "-v",
        "--version",
        callback=version_callback,
        help="Show version and exit",
    ),
):
    """haiku.rag CLI - Vector database RAG system"""
    # Configure logging minimally for CLI context
    if Config.ENV == "development":
        # Lazy import logfire only in development
        try:
            import logfire  # type: ignore

            logfire.configure(send_to_logfire="if-token-present")
            logfire.instrument_pydantic_ai()
        except Exception:
            pass
    else:
        configure_cli_logging()
        warnings.filterwarnings("ignore")

    # Run version check before any command
    try:
        asyncio.run(check_version())
    except Exception:
        # Do not block CLI on version check issues
        pass


@cli.command("list", help="List all stored documents")
def list_documents(
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.list_documents())


def _parse_meta_options(meta: list[str] | None) -> dict[str, Any]:
    """Parse repeated --meta KEY=VALUE options into a dictionary.

    Raises a Typer error if any entry is malformed.
    """
    result: dict[str, Any] = {}
    if not meta:
        return result
    for item in meta:
        if "=" not in item:
            raise typer.BadParameter("--meta must be in KEY=VALUE format")
        key, value = item.split("=", 1)
        if not key:
            raise typer.BadParameter("--meta key cannot be empty")
        # Best-effort JSON coercion: numbers, booleans, null, arrays/objects
        try:
            parsed = json.loads(value)
            result[key] = parsed
        except Exception:
            # Leave as string if not valid JSON literal
            result[key] = value
    return result


@cli.command("add", help="Add a document from text input")
def add_document_text(
    text: str = typer.Argument(
        help="The text content of the document to add",
    ),
    meta: list[str] | None = typer.Option(
        None,
        "--meta",
        help="Metadata entries as KEY=VALUE (repeatable)",
        metavar="KEY=VALUE",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    metadata = _parse_meta_options(meta)
    asyncio.run(app.add_document_from_text(text=text, metadata=metadata or None))


@cli.command("add-src", help="Add a document from a file path, directory, or URL")
def add_document_src(
    source: str = typer.Argument(
        help="The file path, directory, or URL of the document(s) to add",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Optional human-readable title to store with the document",
    ),
    meta: list[str] | None = typer.Option(
        None,
        "--meta",
        help="Metadata entries as KEY=VALUE (repeatable)",
        metavar="KEY=VALUE",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    metadata = _parse_meta_options(meta)
    asyncio.run(
        app.add_document_from_source(
            source=source, title=title, metadata=metadata or None
        )
    )


@cli.command("get", help="Get and display a document by its ID")
def get_document(
    doc_id: str = typer.Argument(
        help="The ID of the document to get",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.get_document(doc_id=doc_id))


@cli.command("delete", help="Delete a document by its ID")
def delete_document(
    doc_id: str = typer.Argument(
        help="The ID of the document to delete",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.delete_document(doc_id=doc_id))


# Add alias `rm` for delete
cli.command("rm", help="Alias for delete: remove a document by its ID")(delete_document)


@cli.command("search", help="Search for documents by a query")
def search(
    query: str = typer.Argument(
        help="The search query to use",
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        "-l",
        help="Maximum number of results to return",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.search(query=query, limit=limit))


@cli.command("ask", help="Ask a question using the QA agent")
def ask(
    question: str = typer.Argument(
        help="The question to ask",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
    cite: bool = typer.Option(
        False,
        "--cite",
        help="Include citations in the response",
    ),
    deep: bool = typer.Option(
        False,
        "--deep",
        help="Use deep multi-agent QA for complex questions",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show verbose progress output (only with --deep)",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.ask(question=question, cite=cite, deep=deep, verbose=verbose))


@cli.command("research", help="Run multi-agent research and output a concise report")
def research(
    question: str = typer.Argument(
        help="The research question to investigate",
    ),
    max_iterations: int = typer.Option(
        3,
        "--max-iterations",
        "-n",
        help="Maximum search/analyze iterations",
    ),
    confidence_threshold: float = typer.Option(
        0.8,
        "--confidence-threshold",
        help="Minimum confidence (0-1) to stop",
    ),
    max_concurrency: int = typer.Option(
        1,
        "--max-concurrency",
        help="Max concurrent searches per iteration (planned)",
    ),
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show verbose progress output",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(
        app.research(
            question=question,
            max_iterations=max_iterations,
            confidence_threshold=confidence_threshold,
            max_concurrency=max_concurrency,
            verbose=verbose,
        )
    )


@cli.command("settings", help="Display current configuration settings")
def settings():
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=Path())  # Don't need actual DB for settings
    app.show_settings()


@cli.command(
    "rebuild",
    help="Rebuild the database by deleting all chunks and re-indexing all documents",
)
def rebuild(
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.rebuild())


@cli.command("vacuum", help="Optimize and clean up all tables to reduce disk usage")
def vacuum(
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.vacuum())


@cli.command("info", help="Show read-only database info (no upgrades or writes)")
def info(
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
):
    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)
    asyncio.run(app.info())


@cli.command("download-models", help="Download Docling and Ollama models per config")
def download_models_cmd():
    from haiku.rag.utils import prefetch_models

    try:
        prefetch_models()
        typer.echo("Models downloaded successfully.")
    except Exception as e:
        typer.echo(f"Error downloading models: {e}")
        raise typer.Exit(1)


@cli.command(
    "serve",
    help="Start haiku.rag server. Use --monitor, --mcp, and/or --a2a to enable services.",
)
def serve(
    db: Path = typer.Option(
        Config.DEFAULT_DATA_DIR / "haiku.rag.lancedb",
        "--db",
        help="Path to the LanceDB database file",
    ),
    monitor: bool = typer.Option(
        False,
        "--monitor",
        help="Enable file monitoring",
    ),
    mcp: bool = typer.Option(
        False,
        "--mcp",
        help="Enable MCP server",
    ),
    stdio: bool = typer.Option(
        False,
        "--stdio",
        help="Run MCP server on stdio Transport (requires --mcp)",
    ),
    mcp_port: int = typer.Option(
        8001,
        "--mcp-port",
        help="Port to bind MCP server to (ignored with --stdio)",
    ),
    a2a: bool = typer.Option(
        False,
        "--a2a",
        help="Enable A2A (Agent-to-Agent) server",
    ),
    a2a_host: str = typer.Option(
        "127.0.0.1",
        "--a2a-host",
        help="Host to bind A2A server to",
    ),
    a2a_port: int = typer.Option(
        8000,
        "--a2a-port",
        help="Port to bind A2A server to",
    ),
) -> None:
    """Start the server with selected services."""
    # Require at least one service flag
    if not (monitor or mcp or a2a):
        typer.echo(
            "Error: At least one service flag (--monitor, --mcp, or --a2a) must be specified"
        )
        raise typer.Exit(1)

    if stdio and not mcp:
        typer.echo("Error: --stdio requires --mcp")
        raise typer.Exit(1)

    from haiku.rag.app import HaikuRAGApp

    app = HaikuRAGApp(db_path=db)

    transport = "stdio" if stdio else None

    asyncio.run(
        app.serve(
            enable_monitor=monitor,
            enable_mcp=mcp,
            mcp_transport=transport,
            mcp_port=mcp_port,
            enable_a2a=a2a,
            a2a_host=a2a_host,
            a2a_port=a2a_port,
        )
    )


@cli.command("migrate", help="Migrate an SQLite database to LanceDB")
def migrate(
    sqlite_path: Path = typer.Argument(
        help="Path to the SQLite database file to migrate",
    ),
):
    # Generate LanceDB path in same parent directory
    lancedb_path = sqlite_path.parent / (sqlite_path.stem + ".lancedb")

    # Lazy import to avoid heavy deps on simple invocations
    from haiku.rag.migration import migrate_sqlite_to_lancedb

    success = asyncio.run(migrate_sqlite_to_lancedb(sqlite_path, lancedb_path))

    if not success:
        raise typer.Exit(1)


@cli.command(
    "a2aclient", help="Run interactive client to chat with haiku.rag's A2A server"
)
def a2aclient(
    url: str = typer.Option(
        "http://localhost:8000",
        "--url",
        help="Base URL of the A2A server",
    ),
):
    try:
        from haiku.rag.a2a.client import run_interactive_client
    except ImportError:
        typer.echo(
            "Error: A2A support requires the 'a2a' extra. "
            "Install with: uv pip install 'haiku.rag[a2a]'"
        )
        raise typer.Exit(1)

    asyncio.run(run_interactive_client(url=url))


if __name__ == "__main__":
    cli()
