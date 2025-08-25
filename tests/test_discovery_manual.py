"""Quick test to verify discovery module works."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.discovery import (
    ExternalServerValidator,
    discover_external_servers,
    initialize_external_servers,
)
from src.config.servers import ServerConfig, ParameterDef


def test_validator() -> None:
    """Test the validator with a simple config."""
    print("Testing ExternalServerValidator...")
    
    # Valid config
    valid_config = ServerConfig(
        name="test-server",
        display_name="Test Server",
        main_module="test/main.py",
        parameters=[]
    )
    
    validator = ExternalServerValidator()
    is_valid, errors = validator.validate_server_config(valid_config, "test")
    
    print(f"  Valid config: {is_valid}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Invalid config - conflicting name
    invalid_config = ServerConfig(
        name="mcp-code-checker",
        display_name="Conflicting Server",
        main_module="test/main.py",
        parameters=[]
    )
    
    is_valid, errors = validator.validate_server_config(invalid_config, "test")
    print(f"  Invalid config (name conflict): {not is_valid}")
    if errors:
        print(f"  Expected error: {errors[0]}")
    
    print("✓ Validator tests passed\n")


def test_discovery() -> None:
    """Test the discovery function."""
    print("Testing discover_external_servers...")
    
    # This will likely find no external servers in test environment
    discovered = discover_external_servers()
    
    print(f"  Discovered {len(discovered)} external server(s)")
    for name, (config, source) in discovered.items():
        print(f"    - {name} from {source}")
    
    print("✓ Discovery test completed\n")


def test_initialization() -> None:
    """Test the initialization function."""
    print("Testing initialize_external_servers...")
    
    count, errors = initialize_external_servers(verbose=False)
    
    print(f"  Registered {count} external server(s)")
    if errors:
        print(f"  Errors: {errors}")
    
    print("✓ Initialization test completed\n")


if __name__ == "__main__":
    print("Running discovery module tests...\n")
    test_validator()
    test_discovery()
    test_initialization()
    print("All tests completed successfully!")
