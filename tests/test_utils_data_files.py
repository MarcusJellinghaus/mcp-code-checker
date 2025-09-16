"""
Tests for the data_files utility module.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_code_checker.utils.data_files import (
    find_data_file,
    find_package_data_files,
    get_package_directory,
)


class TestFindDataFile:
    """Test the find_data_file function."""
    
    def test_find_development_file_new_structure(self):
        """Test finding a file in development environment with new src/ structure."""
        # Create a temporary directory structure matching the new layout
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "src" / "mcp_code_checker" / "resources" / "test_script.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("# test script")
            
            # Should find the development file in new structure
            result = find_data_file(
                package_name="mcp_code_checker.resources",
                relative_path="test_script.py",
                development_base_dir=temp_path,
            )
            
            assert result == test_file
            assert result.exists()

    
    def test_find_installed_file_via_importlib(self):
        """Test finding a file in installed package via importlib."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            test_file = package_dir / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")
            
            # Mock importlib.util.find_spec to return our test location
            mock_spec = MagicMock()
            mock_spec.origin = str(package_dir / "__init__.py")
            
            with patch("mcp_code_checker.utils.data_files.importlib.util.find_spec", return_value=mock_spec):
                result = find_data_file(
                    package_name="test_package",
                    relative_path="data/test_script.py",
                    development_base_dir=None,  # Skip development lookup
                )
                
                assert result == test_file
    
    def test_find_installed_file_via_module_file(self):
        """Test finding a file in installed package via module __file__."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            test_file = package_dir / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")
            
            # Mock the package module
            mock_module = MagicMock()
            mock_module.__file__ = str(package_dir / "__init__.py")
            
            with patch("mcp_code_checker.utils.data_files.importlib.util.find_spec", side_effect=Exception("not found")):
                with patch("mcp_code_checker.utils.data_files.importlib.import_module", return_value=mock_module):
                    result = find_data_file(
                        package_name="test_package",
                        relative_path="data/test_script.py",
                        development_base_dir=None,
                    )
                    
                    assert result == test_file
    
    def test_file_not_found_raises_exception(self):
        """Test that FileNotFoundError is raised when file is not found."""
        with pytest.raises(FileNotFoundError) as exc_info:
            find_data_file(
                package_name="nonexistent_package",
                relative_path="data/missing_script.py",
                development_base_dir=Path("/nonexistent/path"),
            )
        
        assert "not found" in str(exc_info.value).lower()
        assert "data/missing_script.py" in str(exc_info.value)
    
    def test_pyproject_toml_consistency(self):
        """Test that the package configuration in pyproject.toml matches actual usage."""
        import configparser
        import tomllib
        from pathlib import Path
        
        # Read pyproject.toml
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        
        # Get package data configuration
        package_data = pyproject_data.get("tool", {}).get("setuptools", {}).get("package-data", {})
        
        # Check that mcp_code_checker.resources is configured
        resources_config = package_data.get("mcp_code_checker.resources", [])
        assert "sleep_script.py" in resources_config, f"sleep_script.py not found in pyproject.toml package-data. Found: {resources_config}"
        
        # Verify the actual file exists in the expected location
        project_root = Path(__file__).parent.parent
        actual_file = project_root / "src" / "mcp_code_checker" / "resources" / "sleep_script.py"
        assert actual_file.exists(), f"sleep_script.py not found at {actual_file}"
        
        # Test that find_data_file can actually find it
        result = find_data_file(
            package_name="mcp_code_checker.resources",
            relative_path="sleep_script.py",
            development_base_dir=project_root,
        )
        assert result == actual_file


class TestFindPackageDataFiles:
    """Test the find_package_data_files function."""
    
    def test_find_multiple_files(self):
        """Test finding multiple data files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple test files in the new src structure
            files = [
                temp_path / "src" / "mcp_code_checker" / "resources" / "script1.py",
                temp_path / "src" / "mcp_code_checker" / "resources" / "defaults.json",
            ]
            
            for file_path in files:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("# test content")
            
            result = find_package_data_files(
                package_name="mcp_code_checker.resources",
                relative_paths=["script1.py", "defaults.json"],
                development_base_dir=temp_path,
            )
            
            assert len(result) == 2
            assert result[0] == files[0]
            assert result[1] == files[1]


class TestGetPackageDirectory:
    """Test the get_package_directory function."""
    
    def test_get_directory_via_importlib(self):
        """Test getting package directory via importlib."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            package_dir.mkdir()
            
            mock_spec = MagicMock()
            mock_spec.origin = str(package_dir / "__init__.py")
            
            with patch("mcp_code_checker.utils.data_files.importlib.util.find_spec", return_value=mock_spec):
                result = get_package_directory("test_package")
                assert result == package_dir
    
    def test_get_directory_via_module_file(self):
        """Test getting package directory via module __file__."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            package_dir.mkdir()
            
            mock_module = MagicMock()
            mock_module.__file__ = str(package_dir / "__init__.py")
            
            with patch("mcp_code_checker.utils.data_files.importlib.util.find_spec", side_effect=Exception("not found")):
                with patch("mcp_code_checker.utils.data_files.importlib.import_module", return_value=mock_module):
                    result = get_package_directory("test_package")
                    assert result == package_dir
    
    def test_package_not_found_raises_exception(self):
        """Test that ImportError is raised when package is not found."""
        with patch("mcp_code_checker.utils.data_files.importlib.util.find_spec", side_effect=Exception("not found")):
            with patch("mcp_code_checker.utils.data_files.importlib.import_module", side_effect=ImportError("no module")):
                with pytest.raises(ImportError) as exc_info:
                    get_package_directory("nonexistent_package")
                
                assert "Cannot find package directory" in str(exc_info.value)
