#!/usr/bin/env python3
"""
SMCP Server Entry Point

This module provides the command-line entry point for running the SMCP (Scientific Model Context Protocol) server.
It creates a minimal SMCP server that exposes all ToolUniverse tools as MCP tools.
"""

import argparse
import sys
from .smcp import SMCP


def run_http_server():
    """
    Run SMCP server with streamable-http transport on localhost:8000

    This function provides compatibility with the original MCP server's run_server function.
    """
    parser = argparse.ArgumentParser(
        description="Start SMCP (Scientific Model Context Protocol) Server with HTTP transport",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with all tools using HTTP transport
  tooluniverse-smcp-server

  # Start with specific categories
  tooluniverse-smcp-server --categories uniprot ChEMBL opentarget

  # Start with hooks enabled
  tooluniverse-smcp-server --hooks-enabled

  # Start with specific hook type
  tooluniverse-smcp-server --hook-type SummarizationHook

  # Start with custom hook configuration
  tooluniverse-smcp-server --hook-config-file /path/to/hook_config.json
        """,
    )

    # Hook configuration options
    hook_group = parser.add_argument_group("Hook Configuration")
    hook_group.add_argument(
        "--hooks-enabled",
        action="store_true",
        help="Enable output processing hooks (default: False)",
    )
    hook_group.add_argument(
        "--hook-type",
        choices=["SummarizationHook", "FileSaveHook"],
        help="Simple hook type selection (SummarizationHook or FileSaveHook)",
    )
    hook_group.add_argument(
        "--hook-config-file",
        type=str,
        help="Path to custom hook configuration JSON file",
    )

    # Server configuration options
    server_group = parser.add_argument_group("Server Configuration")
    server_group.add_argument(
        "--host", default="127.0.0.1", help="Server host address (default: 127.0.0.1)"
    )
    server_group.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    server_group.add_argument(
        "--name",
        default="ToolUniverse SMCP Server",
        help="Server name (default: ToolUniverse SMCP Server)",
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting ToolUniverse SMCP Server...")
        print("📡 Transport: streamable-http")
        print(f"🌐 Address: http://{args.host}:{args.port}")
        print(f"🏷️  Name: {args.name}")

        # Load hook configuration if specified
        hook_config = None
        if args.hook_config_file:
            import json

            with open(args.hook_config_file, "r") as f:
                hook_config = json.load(f)
            print(f"🔗 Hook config loaded from: {args.hook_config_file}")

        # Determine hook settings
        hooks_enabled = (
            args.hooks_enabled or args.hook_type is not None or hook_config is not None
        )
        if hooks_enabled:
            if args.hook_type:
                print(f"🔗 Hooks enabled: {args.hook_type}")
            elif hook_config:
                hook_count = len(hook_config.get("hooks", []))
                print(f"🔗 Hooks enabled: {hook_count} custom hooks")
            else:
                print("🔗 Hooks enabled: default configuration")
        else:
            print("🔗 Hooks disabled")

        print()

        # Create SMCP server with hook support
        server = SMCP(
            name=args.name,
            auto_expose_tools=True,
            search_enabled=True,
            max_workers=5,
            hooks_enabled=hooks_enabled,
            hook_config=hook_config,
            hook_type=args.hook_type,
        )

        # Run server with streamable-http transport
        server.run_simple(transport="http", host=args.host, port=args.port)

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


def run_stdio_server():
    """
    Run SMCP server with stdio transport for Claude Desktop integration

    This function provides compatibility with the original MCP server's run_claude_desktop function.
    It accepts the same arguments as run_smcp_server but forces transport='stdio'.
    """
    parser = argparse.ArgumentParser(
        description="Start SMCP (Scientific Model Context Protocol) Server with stdio transport",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with all tools using stdio transport (hooks enabled by default)
  tooluniverse-stdio

  # Start with specific categories
  tooluniverse-stdio --categories uniprot ChEMBL opentarget

  # Enable hooks
  tooluniverse-stdio --hooks

  # Use FileSaveHook instead of SummarizationHook
  tooluniverse-stdio --hook-type FileSaveHook

  # Use custom hook configuration
  tooluniverse-stdio --hook-config-file /path/to/hook_config.json

  # Start with categories but exclude specific tools
  tooluniverse-stdio --categories uniprot ChEMBL --exclude-tools "ChEMBL_get_molecule_by_chembl_id"

  # Start with all tools but exclude entire categories
  tooluniverse-stdio --exclude-categories mcp_auto_loader_boltz mcp_auto_loader_expert_feedback

  # Load only specific tools by name
  tooluniverse-stdio --include-tools "UniProt_get_entry_by_accession" "ChEMBL_get_molecule_by_chembl_id"

  # Load tools from a file
  tooluniverse-stdio --tools-file "/path/to/tool_names.txt"

  # Load additional config files
  tooluniverse-stdio --tool-config-files "custom:/path/to/custom_tools.json"

  # Include/exclude specific tool types
  tooluniverse-stdio --include-tool-types "OpenTarget" "ToolFinderEmbedding"
  tooluniverse-stdio --exclude-tool-types "ToolFinderLLM" "Unknown"

  # List available categories
  tooluniverse-stdio --list-categories

  # List all available tools
  tooluniverse-stdio --list-tools

  # Start minimal server with just search tools
  tooluniverse-stdio --categories special_tools tool_finder
        """,
    )

    # Tool selection options
    tool_group = parser.add_mutually_exclusive_group()
    tool_group.add_argument(
        "--categories",
        nargs="*",
        metavar="CATEGORY",
        help="Specific tool categories to load (e.g., uniprot ChEMBL opentarget). Use --list-categories to see available options.",
    )
    tool_group.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available tool categories and exit",
    )

    # Tool exclusion options
    parser.add_argument(
        "--exclude-tools",
        nargs="*",
        metavar="TOOL_NAME",
        help='Specific tool names to exclude from loading (e.g., "tool1" "tool2"). Can be used with --categories.',
    )
    parser.add_argument(
        "--exclude-categories",
        nargs="*",
        metavar="CATEGORY",
        help="Tool categories to exclude from loading (e.g., mcp_auto_loader_boltz). Can be used with --categories.",
    )

    # Tool inclusion options
    parser.add_argument(
        "--include-tools",
        nargs="*",
        metavar="TOOL_NAME",
        help="Specific tool names to include (only these tools will be loaded). Overrides category selection.",
    )
    parser.add_argument(
        "--tools-file",
        metavar="FILE_PATH",
        help="Path to text file containing tool names to include (one per line). Overrides category selection.",
    )
    parser.add_argument(
        "--tool-config-files",
        nargs="*",
        metavar="CATEGORY:PATH",
        help='Additional tool config files to load. Format: "category:/path/to/config.json"',
    )

    # Tool type filtering options
    parser.add_argument(
        "--include-tool-types",
        nargs="*",
        metavar="TOOL_TYPE",
        help="Specific tool types to include (e.g., OpenTarget ToolFinderEmbedding). Only tools of these types will be loaded.",
    )
    parser.add_argument(
        "--exclude-tool-types",
        nargs="*",
        metavar="TOOL_TYPE",
        help="Tool types to exclude from loading (e.g., ToolFinderLLM Unknown). Useful for excluding specific tool type classes.",
    )

    # Listing options
    parser.add_argument(
        "--list-tools", action="store_true", help="List all available tools and exit"
    )

    # Server configuration (stdio-specific)
    parser.add_argument(
        "--name",
        default="ToolUniverse SMCP Server",
        help="Server name (default: ToolUniverse SMCP Server)",
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Disable intelligent search functionality",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum worker threads for concurrent execution (default: 5)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Hook configuration options (default disabled for stdio)
    hook_group = parser.add_argument_group("Hook Configuration")
    hook_group.add_argument(
        "--hooks",
        action="store_true",
        help="Enable output processing hooks (default: disabled for stdio)",
    )
    hook_group.add_argument(
        "--hook-type",
        choices=["SummarizationHook", "FileSaveHook"],
        help="Hook type to use (default: SummarizationHook when hooks are enabled)",
    )
    hook_group.add_argument(
        "--hook-config-file",
        type=str,
        help="Path to custom hook configuration JSON file",
    )

    args = parser.parse_args()

    # Handle --list-categories
    if args.list_categories:
        try:
            from .execute_function import ToolUniverse

            tu = ToolUniverse()
            tool_types = tu.get_tool_types()

            print("Available tool categories:", file=sys.stderr)
            print("=" * 50, file=sys.stderr)

            # Group categories for better readability
            scientific_db = []
            literature = []
            software = []
            special = []
            clinical = []
            other = []

            for category in sorted(tool_types):
                if category in [
                    "uniprot",
                    "ChEMBL",
                    "opentarget",
                    "pubchem",
                    "hpa",
                    "rcsb_pdb",
                    "reactome",
                    "go",
                ]:
                    scientific_db.append(category)
                elif category in [
                    "EuropePMC",
                    "semantic_scholar",
                    "pubtator",
                    "OpenAlex",
                ]:
                    literature.append(category)
                elif category.startswith("software_"):
                    software.append(category)
                elif category in [
                    "special_tools",
                    "tool_finder",
                    "tool_composition",
                    "agents",
                ]:
                    special.append(category)
                elif category in [
                    "clinical_trials",
                    "fda_drug_label",
                    "fda_drug_adverse_event",
                    "dailymed",
                    "medlineplus",
                ]:
                    clinical.append(category)
                else:
                    other.append(category)

            if scientific_db:
                print("\n🔬 Scientific Databases:", file=sys.stderr)
                for cat in scientific_db:
                    print(f"  {cat}", file=sys.stderr)

            if literature:
                print("\n📚 Literature & Knowledge:", file=sys.stderr)
                for cat in literature:
                    print(f"  {cat}", file=sys.stderr)

            if clinical:
                print("\n🏥 Clinical & Drug Information:", file=sys.stderr)
                for cat in clinical:
                    print(f"  {cat}", file=sys.stderr)

            if software:
                print("\n💻 Software Tools:", file=sys.stderr)
                for cat in software[:5]:  # Show first 5
                    print(f"  {cat}", file=sys.stderr)
                if len(software) > 5:
                    print(
                        f"  ... and {len(software, file=sys.stderr) - 5} more software categories"
                    )

            if special:
                print("\n🛠 Special & Meta Tools:", file=sys.stderr)
                for cat in special:
                    print(f"  {cat}", file=sys.stderr)

            if other:
                print("\n📂 Other Categories:", file=sys.stderr)
                for cat in other:
                    print(f"  {cat}", file=sys.stderr)

            print(f"\nTotal: {len(tool_types, file=sys.stderr)} categories available")
            print("\nCommon combinations:", file=sys.stderr)
            print(
                "  Scientific research: uniprot ChEMBL opentarget pubchem hpa",
                file=sys.stderr,
            )
            print(
                "  Drug discovery: ChEMBL fda_drug_label clinical_trials pubchem",
                file=sys.stderr,
            )
            print(
                "  Literature analysis: EuropePMC semantic_scholar pubtator",
                file=sys.stderr,
            )
            print("  Minimal setup: special_tools tool_finder", file=sys.stderr)

        except Exception as e:
            print(f"❌ Error listing categories: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Handle --list-tools
    if args.list_tools:
        try:
            from .execute_function import ToolUniverse

            tu = ToolUniverse()
            tu.load_tools()  # Load all tools to list them

            print("Available tools:", file=sys.stderr)
            print("=" * 50, file=sys.stderr)

            # Group tools by category
            tools_by_category = {}
            for tool in tu.all_tools:
                tool_type = getattr(tool, "tool_type", "unknown")
                if tool_type not in tools_by_category:
                    tools_by_category[tool_type] = []
                tools_by_category[tool_type].append(tool.name)

            total_tools = 0
            for category in sorted(tools_by_category.keys()):
                tools = sorted(tools_by_category[category])
                print(f"\n📁 {category} ({len(tools, file=sys.stderr)} tools):")
                for tool in tools[:10]:  # Show first 10 tools per category
                    print(f"  {tool}", file=sys.stderr)
                if len(tools) > 10:
                    print(f"  ... and {len(tools, file=sys.stderr) - 10} more tools")
                total_tools += len(tools)

            print(f"\nTotal: {total_tools} tools available", file=sys.stderr)
            print(
                "\nNote: Use --exclude-tools to exclude specific tools by name",
                file=sys.stderr,
            )
            print(
                "      Use --exclude-categories to exclude entire categories",
                file=sys.stderr,
            )

        except Exception as e:
            print(f"❌ Error listing tools: {e}", file=sys.stderr)
            sys.exit(1)
        return

    try:
        print(f"🚀 Starting {args.name}...", file=sys.stderr)
        print("📡 Transport: stdio (for Claude Desktop)", file=sys.stderr)
        print(f"🔍 Search enabled: {not args.no_search}", file=sys.stderr)

        if args.categories is not None:
            if len(args.categories) == 0:
                print("📂 No categories specified, loading all tools", file=sys.stderr)
                tool_categories = None
            else:
                print(
                    f"📂 Tool categories: {', '.join(args.categories)}", file=sys.stderr
                )
                tool_categories = args.categories
        else:
            print("📂 Loading all tool categories", file=sys.stderr)
            tool_categories = None

        # Handle exclusions and inclusions
        exclude_tools = args.exclude_tools or []
        exclude_categories = args.exclude_categories or []
        include_tools = args.include_tools or []
        tools_file = args.tools_file
        include_tool_types = args.include_tool_types or []
        exclude_tool_types = args.exclude_tool_types or []

        # Parse tool config files
        tool_config_files = {}
        if args.tool_config_files:
            for config_spec in args.tool_config_files:
                if ":" in config_spec:
                    category, path = config_spec.split(":", 1)
                    tool_config_files[category] = path
                else:
                    print(
                        f"❌ Invalid tool config file format: {config_spec}",
                        file=sys.stderr,
                    )
                    print(
                        "   Expected format: 'category:/path/to/config.json'",
                        file=sys.stderr,
                    )
                    sys.exit(1)

        if exclude_tools:
            print(f"🚫 Excluding tools: {', '.join(exclude_tools)}", file=sys.stderr)
        if exclude_categories:
            print(
                f"🚫 Excluding categories: {', '.join(exclude_categories)}",
                file=sys.stderr,
            )
        if include_tools:
            print(
                f"✅ Including only specific tools: {len(include_tools)} tools",
                file=sys.stderr,
            )
        if tools_file:
            print(f"📄 Loading tools from file: {tools_file}", file=sys.stderr)
        if tool_config_files:
            print(
                f"📦 Additional config files: {', '.join(tool_config_files.keys())}",
                file=sys.stderr,
            )
        if include_tool_types:
            print(
                f"🎯 Including tool types: {', '.join(include_tool_types)}",
                file=sys.stderr,
            )
        if exclude_tool_types:
            print(
                f"🚫 Excluding tool types: {', '.join(exclude_tool_types)}",
                file=sys.stderr,
            )

        # Load hook configuration if specified
        hook_config = None
        if args.hook_config_file:
            import json

            with open(args.hook_config_file, "r") as f:
                hook_config = json.load(f)
            print(
                f"🔗 Hook config loaded from: {args.hook_config_file}", file=sys.stderr
            )

        # Determine hook settings (default disabled for stdio)
        hooks_enabled = (
            args.hooks or args.hook_type is not None or hook_config is not None
        )

        # Set default hook type if hooks are enabled but no type specified
        hook_type = args.hook_type
        if hooks_enabled and hook_type is None:
            hook_type = "SummarizationHook"
        if hooks_enabled:
            if hook_type:
                print(f"🔗 Hooks enabled: {hook_type}", file=sys.stderr)
            elif hook_config:
                hook_count = len(hook_config.get("hooks", []))
                print(f"🔗 Hooks enabled: {hook_count} custom hooks", file=sys.stderr)
            else:
                print("🔗 Hooks enabled: default configuration", file=sys.stderr)
        else:
            print("🔗 Hooks disabled", file=sys.stderr)

        print(f"⚡ Max workers: {args.max_workers}", file=sys.stderr)
        print()

        # Create SMCP server with hook support
        server = SMCP(
            name=args.name,
            tool_categories=tool_categories,
            exclude_tools=exclude_tools,
            exclude_categories=exclude_categories,
            include_tools=include_tools,
            tools_file=tools_file,
            tool_config_files=tool_config_files,
            include_tool_types=include_tool_types,
            exclude_tool_types=exclude_tool_types,
            search_enabled=not args.no_search,
            max_workers=args.max_workers,
            hooks_enabled=hooks_enabled,
            hook_config=hook_config,
            hook_type=hook_type,
        )

        # Run server with stdio transport (forced)
        server.run_simple(transport="stdio")

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def run_smcp_server():
    """
    Main entry point for the SMCP server command.

    This function is called when running `tooluniverse-smcp` from the command line.
    """
    parser = argparse.ArgumentParser(
        description="Start SMCP (Scientific Model Context Protocol) Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with all tools on port 7890
  tooluniverse-smcp --port 7890

  # Start with specific categories
  tooluniverse-smcp --categories uniprot ChEMBL opentarget --port 8000

  # Start with categories but exclude specific tools
  tooluniverse-smcp --categories uniprot ChEMBL --exclude-tools "ChEMBL_get_molecule_by_chembl_id" --port 8000

  # Start with all tools but exclude entire categories
  tooluniverse-smcp --exclude-categories mcp_auto_loader_boltz mcp_auto_loader_expert_feedback --port 8000

  # Load only specific tools by name
  tooluniverse-smcp --include-tools "UniProt_get_entry_by_accession" "ChEMBL_get_molecule_by_chembl_id" --port 8000

  # Load tools from a file
  tooluniverse-smcp --tools-file "/path/to/tool_names.txt" --port 8000

  # Load additional config files
  tooluniverse-smcp --tool-config-files "custom:/path/to/custom_tools.json" --port 8000

  # Include/exclude specific tool types
  tooluniverse-smcp --include-tool-types "OpenTarget" "ToolFinderEmbedding" --port 8000
  tooluniverse-smcp --exclude-tool-types "ToolFinderLLM" "Unknown" --port 8000

  # List available categories
  tooluniverse-smcp --list-categories

  # List all available tools
  tooluniverse-smcp --list-tools

  # Start minimal server with just search tools
  tooluniverse-smcp --categories special_tools tool_finder --port 7000

  # Start server for Claude Desktop (stdio transport)
  tooluniverse-smcp --transport stdio
        """,
    )

    # Tool selection options
    tool_group = parser.add_mutually_exclusive_group()
    tool_group.add_argument(
        "--categories",
        nargs="*",
        metavar="CATEGORY",
        help="Specific tool categories to load (e.g., uniprot ChEMBL opentarget). Use --list-categories to see available options.",
    )
    tool_group.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available tool categories and exit",
    )

    # Tool exclusion options
    parser.add_argument(
        "--exclude-tools",
        nargs="*",
        metavar="TOOL_NAME",
        help='Specific tool names to exclude from loading (e.g., "tool1" "tool2"). Can be used with --categories.',
    )
    parser.add_argument(
        "--exclude-categories",
        nargs="*",
        metavar="CATEGORY",
        help="Tool categories to exclude from loading (e.g., mcp_auto_loader_boltz). Can be used with --categories.",
    )

    # Tool inclusion options
    parser.add_argument(
        "--include-tools",
        nargs="*",
        metavar="TOOL_NAME",
        help="Specific tool names to include (only these tools will be loaded). Overrides category selection.",
    )
    parser.add_argument(
        "--tools-file",
        metavar="FILE_PATH",
        help="Path to text file containing tool names to include (one per line). Overrides category selection.",
    )
    parser.add_argument(
        "--tool-config-files",
        nargs="*",
        metavar="CATEGORY:PATH",
        help='Additional tool config files to load. Format: "category:/path/to/config.json"',
    )

    # Tool type filtering options
    parser.add_argument(
        "--include-tool-types",
        nargs="*",
        metavar="TOOL_TYPE",
        help="Specific tool types to include (e.g., OpenTarget ToolFinderEmbedding). Only tools of these types will be loaded.",
    )
    parser.add_argument(
        "--exclude-tool-types",
        nargs="*",
        metavar="TOOL_TYPE",
        help="Tool types to exclude from loading (e.g., ToolFinderLLM Unknown). Useful for excluding specific tool type classes.",
    )

    # Listing options
    parser.add_argument(
        "--list-tools", action="store_true", help="List all available tools and exit"
    )

    # Server configuration
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="http",
        help="Transport protocol to use (default: http)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to for HTTP/SSE transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7000,
        help="Port to bind to for HTTP/SSE transport (default: 7000)",
    )
    parser.add_argument(
        "--name",
        default="ToolUniverse SMCP Server",
        help="Server name (default: ToolUniverse SMCP Server)",
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Disable intelligent search functionality",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum worker threads for concurrent execution (default: 5)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Hook configuration options
    hook_group = parser.add_argument_group("Hook Configuration")
    hook_group.add_argument(
        "--hooks-enabled",
        action="store_true",
        help="Enable output processing hooks (default: False)",
    )
    hook_group.add_argument(
        "--hook-type",
        choices=["SummarizationHook", "FileSaveHook"],
        help="Simple hook type selection (SummarizationHook or FileSaveHook)",
    )
    hook_group.add_argument(
        "--hook-config-file",
        type=str,
        help="Path to custom hook configuration JSON file",
    )

    args = parser.parse_args()

    # Handle --list-categories
    if args.list_categories:
        try:
            from .execute_function import ToolUniverse

            tu = ToolUniverse()
            tool_types = tu.get_tool_types()

            print("Available tool categories:")
            print("=" * 50)

            # Group categories for better readability
            scientific_db = []
            literature = []
            software = []
            special = []
            clinical = []
            other = []

            for category in sorted(tool_types):
                if category in [
                    "uniprot",
                    "ChEMBL",
                    "opentarget",
                    "pubchem",
                    "hpa",
                    "rcsb_pdb",
                    "reactome",
                    "go",
                ]:
                    scientific_db.append(category)
                elif category in [
                    "EuropePMC",
                    "semantic_scholar",
                    "pubtator",
                    "OpenAlex",
                ]:
                    literature.append(category)
                elif category.startswith("software_"):
                    software.append(category)
                elif category in [
                    "special_tools",
                    "tool_finder",
                    "tool_composition",
                    "agents",
                ]:
                    special.append(category)
                elif category in [
                    "clinical_trials",
                    "fda_drug_label",
                    "fda_drug_adverse_event",
                    "dailymed",
                    "medlineplus",
                ]:
                    clinical.append(category)
                else:
                    other.append(category)

            if scientific_db:
                print("\n🔬 Scientific Databases:")
                for cat in scientific_db:
                    print(f"  {cat}")

            if literature:
                print("\n📚 Literature & Knowledge:")
                for cat in literature:
                    print(f"  {cat}")

            if clinical:
                print("\n🏥 Clinical & Drug Information:")
                for cat in clinical:
                    print(f"  {cat}")

            if software:
                print("\n💻 Software Tools:")
                for cat in software[:5]:  # Show first 5
                    print(f"  {cat}")
                if len(software) > 5:
                    print(f"  ... and {len(software) - 5} more software categories")

            if special:
                print("\n🛠 Special & Meta Tools:")
                for cat in special:
                    print(f"  {cat}")

            if other:
                print("\n📂 Other Categories:")
                for cat in other:
                    print(f"  {cat}")

            print(f"\nTotal: {len(tool_types)} categories available")
            print("\nCommon combinations:")
            print("  Scientific research: uniprot ChEMBL opentarget pubchem hpa")
            print("  Drug discovery: ChEMBL fda_drug_label clinical_trials pubchem")
            print("  Literature analysis: EuropePMC semantic_scholar pubtator")
            print("  Minimal setup: special_tools tool_finder")

        except Exception as e:
            print(f"❌ Error listing categories: {e}")
            sys.exit(1)
        return

    # Handle --list-tools
    if args.list_tools:
        try:
            from .execute_function import ToolUniverse

            tu = ToolUniverse()
            tu.load_tools()  # Load all tools to list them

            print("Available tools:")
            print("=" * 50)

            # Group tools by category
            tools_by_category = {}
            for tool in tu.all_tools:
                tool_type = getattr(tool, "tool_type", "unknown")
                if tool_type not in tools_by_category:
                    tools_by_category[tool_type] = []
                tools_by_category[tool_type].append(tool.name)

            total_tools = 0
            for category in sorted(tools_by_category.keys()):
                tools = sorted(tools_by_category[category])
                print(f"\n📁 {category} ({len(tools)} tools):")
                for tool in tools[:10]:  # Show first 10 tools per category
                    print(f"  {tool}")
                if len(tools) > 10:
                    print(f"  ... and {len(tools) - 10} more tools")
                total_tools += len(tools)

            print(f"\nTotal: {total_tools} tools available")
            print("\nNote: Use --exclude-tools to exclude specific tools by name")
            print("      Use --exclude-categories to exclude entire categories")

        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            sys.exit(1)
        return

    try:
        print(f"🚀 Starting {args.name}...")
        print(f"📡 Transport: {args.transport}")
        if args.transport in ["http", "sse"]:
            print(f"🌐 Address: http://{args.host}:{args.port}")
        print(f"🔍 Search enabled: {not args.no_search}")

        if args.categories is not None:
            if len(args.categories) == 0:
                print("📂 No categories specified, loading all tools")
                tool_categories = None
            else:
                print(f"📂 Tool categories: {', '.join(args.categories)}")
                tool_categories = args.categories
        else:
            print("📂 Loading all tool categories")
            tool_categories = None

        # Handle exclusions and inclusions
        exclude_tools = args.exclude_tools or []
        exclude_categories = args.exclude_categories or []
        include_tools = args.include_tools or []
        tools_file = args.tools_file
        include_tool_types = args.include_tool_types or []
        exclude_tool_types = args.exclude_tool_types or []

        # Parse tool config files
        tool_config_files = {}
        if args.tool_config_files:
            for config_spec in args.tool_config_files:
                if ":" in config_spec:
                    category, path = config_spec.split(":", 1)
                    tool_config_files[category] = path
                else:
                    print(f"❌ Invalid tool config file format: {config_spec}")
                    print("   Expected format: 'category:/path/to/config.json'")
                    sys.exit(1)

        if exclude_tools:
            print(f"🚫 Excluding tools: {', '.join(exclude_tools)}")
        if exclude_categories:
            print(f"🚫 Excluding categories: {', '.join(exclude_categories)}")
        if include_tools:
            print(f"✅ Including only specific tools: {len(include_tools)} tools")
        if tools_file:
            print(f"📄 Loading tools from file: {tools_file}")
        if tool_config_files:
            print(f"📦 Additional config files: {', '.join(tool_config_files.keys())}")
        if include_tool_types:
            print(f"🎯 Including tool types: {', '.join(include_tool_types)}")
        if exclude_tool_types:
            print(f"🚫 Excluding tool types: {', '.join(exclude_tool_types)}")

        # Load hook configuration if specified
        hook_config = None
        if args.hook_config_file:
            import json

            with open(args.hook_config_file, "r") as f:
                hook_config = json.load(f)
            print(f"🔗 Hook config loaded from: {args.hook_config_file}")

        # Determine hook settings
        hooks_enabled = (
            args.hooks_enabled or args.hook_type is not None or hook_config is not None
        )
        if hooks_enabled:
            if args.hook_type:
                print(f"🔗 Hooks enabled: {args.hook_type}")
            elif hook_config:
                hook_count = len(hook_config.get("hooks", []))
                print(f"🔗 Hooks enabled: {hook_count} custom hooks")
            else:
                print("🔗 Hooks enabled: default configuration")
        else:
            print("🔗 Hooks disabled")

        print(f"⚡ Max workers: {args.max_workers}")
        print()

        # Create SMCP server with hook support
        server = SMCP(
            name=args.name,
            tool_categories=tool_categories,
            exclude_tools=exclude_tools,
            exclude_categories=exclude_categories,
            include_tools=include_tools,
            tools_file=tools_file,
            tool_config_files=tool_config_files,
            include_tool_types=include_tool_types,
            exclude_tool_types=exclude_tool_types,
            search_enabled=not args.no_search,
            max_workers=args.max_workers,
            hooks_enabled=hooks_enabled,
            hook_config=hook_config,
            hook_type=args.hook_type,
        )

        # Run server
        server.run_simple(transport=args.transport, host=args.host, port=args.port)

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_smcp_server()
