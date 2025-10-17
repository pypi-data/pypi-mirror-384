#!/usr/bin/env python3
"""Test script to validate MCP server structure without running it."""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        import logging
        print("✓ logging")
    except ImportError as e:
        print(f"✗ logging: {e}")
        return False

    try:
        import asyncio
        print("✓ asyncio")
    except ImportError as e:
        print(f"✗ asyncio: {e}")
        return False

    try:
        from pathlib import Path
        print("✓ pathlib")
    except ImportError as e:
        print(f"✗ pathlib: {e}")
        return False

    return True

def test_browser_agent():
    """Test browser_agent.py can be parsed."""
    print("\nTesting browser_agent.py...")

    try:
        import ast
        browser_agent_path = Path(__file__).parent / "browser_agent.py"
        with open(browser_agent_path) as f:
            ast.parse(f.read())
        print("✓ browser_agent.py syntax valid")
        return True
    except SyntaxError as e:
        print(f"✗ browser_agent.py syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ browser_agent.py error: {e}")
        return False

def test_server():
    """Test server.py can be parsed."""
    print("\nTesting server.py...")

    try:
        import ast
        server_path = Path(__file__).parent / "server.py"
        with open(server_path) as f:
            ast.parse(f.read())
        print("✓ server.py syntax valid")
        return True
    except SyntaxError as e:
        print(f"✗ server.py syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ server.py error: {e}")
        return False

def test_dependencies():
    """Check for required external dependencies."""
    print("\nChecking external dependencies...")

    deps = {
        "mcp": "mcp[cli]",
        "google.genai": "google-genai",
        "playwright.sync_api": "playwright",
        "dotenv": "python-dotenv"
    }

    all_found = True
    for module_name, package_name in deps.items():
        try:
            __import__(module_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} (install with: uv pip install {package_name})")
            all_found = False

    return all_found

def test_config_files():
    """Check for required configuration files."""
    print("\nChecking configuration files...")

    files = [
        "pyproject.toml",
        ".env.sample",
        "README.md",
    ]

    all_found = True
    base_path = Path(__file__).parent
    for filename in files:
        file_path = base_path / filename
        if file_path.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} missing")
            all_found = False

    return all_found

def main():
    """Run all tests."""
    print("=" * 60)
    print("Gemini Computer Use MCP Server - Validation Tests")
    print("=" * 60)

    tests = [
        ("Standard library imports", test_imports),
        ("Browser agent module", test_browser_agent),
        ("Server module", test_server),
        ("Configuration files", test_config_files),
        ("External dependencies", test_dependencies),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All validation tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: uv sync")
        print("2. Install Playwright: playwright install chromium")
        print("3. Configure .env: cp .env.sample .env && edit .env")
        print("4. Test with MCP Inspector: uv run mcp dev server.py")
        print("5. Install in Claude Desktop: uv run mcp install server.py")
        return 0
    else:
        print("✗ Some validation tests failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
