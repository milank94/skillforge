"""Tests for the command simulator."""

from unittest.mock import Mock

import pytest

from skillforge.core.simulator import CommandSimulator, VirtualFileSystem


class TestVirtualFileSystem:
    """Tests for VirtualFileSystem."""

    def test_initialization(self):
        """Test file system initialization."""
        fs = VirtualFileSystem()
        assert fs.current_dir == "/home/user"
        assert "/" in fs.directories
        assert "/home" in fs.directories
        assert "/home/user" in fs.directories
        assert len(fs.files) == 0

    def test_normalize_path_absolute(self):
        """Test normalization of absolute paths."""
        fs = VirtualFileSystem()
        assert fs.normalize_path("/home/user/file.txt") == "/home/user/file.txt"
        assert fs.normalize_path("/tmp") == "/tmp"
        assert fs.normalize_path("/") == "/"

    def test_normalize_path_relative(self):
        """Test normalization of relative paths."""
        fs = VirtualFileSystem()
        fs.current_dir = "/home/user"
        assert fs.normalize_path("file.txt") == "/home/user/file.txt"
        assert fs.normalize_path("docs/readme.md") == "/home/user/docs/readme.md"

    def test_normalize_path_with_dots(self):
        """Test path normalization with . and .."""
        fs = VirtualFileSystem()
        assert fs.normalize_path("/home/user/../tmp") == "/home/tmp"
        assert fs.normalize_path("/home/user/./file.txt") == "/home/user/file.txt"
        assert fs.normalize_path("/home/user/docs/../file.txt") == "/home/user/file.txt"

    def test_write_and_read_file(self):
        """Test writing and reading files."""
        fs = VirtualFileSystem()
        fs.write_file("/home/user/test.txt", "Hello, World!")
        content = fs.read_file("/home/user/test.txt")
        assert content == "Hello, World!"

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        fs = VirtualFileSystem()
        with pytest.raises(FileNotFoundError):
            fs.read_file("/home/user/nonexistent.txt")

    def test_file_exists(self):
        """Test checking if files exist."""
        fs = VirtualFileSystem()
        fs.write_file("/home/user/test.txt", "content")
        assert fs.exists("/home/user/test.txt")
        assert not fs.exists("/home/user/nonexistent.txt")

    def test_is_file(self):
        """Test checking if path is a file."""
        fs = VirtualFileSystem()
        fs.write_file("/home/user/test.txt", "content")
        assert fs.is_file("/home/user/test.txt")
        assert not fs.is_file("/home/user")

    def test_is_directory(self):
        """Test checking if path is a directory."""
        fs = VirtualFileSystem()
        assert fs.is_directory("/home/user")
        assert not fs.is_directory("/home/user/nonexistent")

    def test_create_directory(self):
        """Test creating directories."""
        fs = VirtualFileSystem()
        fs.create_directory("/home/user/projects")
        assert fs.is_directory("/home/user/projects")

    def test_create_nested_directory(self):
        """Test creating nested directories."""
        fs = VirtualFileSystem()
        fs.create_directory("/home/user/projects/python/myapp")
        assert fs.is_directory("/home/user/projects")
        assert fs.is_directory("/home/user/projects/python")
        assert fs.is_directory("/home/user/projects/python/myapp")

    def test_touch_creates_empty_file(self):
        """Test touch creates an empty file."""
        fs = VirtualFileSystem()
        fs.touch("/home/user/newfile.txt")
        assert fs.is_file("/home/user/newfile.txt")
        assert fs.read_file("/home/user/newfile.txt") == ""

    def test_list_directory(self):
        """Test listing directory contents."""
        fs = VirtualFileSystem()
        fs.write_file("/home/user/file1.txt", "content1")
        fs.write_file("/home/user/file2.txt", "content2")
        fs.create_directory("/home/user/subdir")

        contents = fs.list_directory("/home/user")
        assert "file1.txt" in contents
        assert "file2.txt" in contents
        assert "subdir" in contents

    def test_list_empty_directory(self):
        """Test listing an empty directory."""
        fs = VirtualFileSystem()
        fs.create_directory("/home/user/empty")
        contents = fs.list_directory("/home/user/empty")
        assert contents == []

    def test_list_nonexistent_directory(self):
        """Test listing a directory that doesn't exist."""
        fs = VirtualFileSystem()
        with pytest.raises(FileNotFoundError):
            fs.list_directory("/nonexistent")

    def test_list_file_as_directory(self):
        """Test listing a file as if it were a directory."""
        fs = VirtualFileSystem()
        fs.write_file("/home/user/file.txt", "content")
        with pytest.raises(NotADirectoryError):
            fs.list_directory("/home/user/file.txt")


class TestCommandSimulator:
    """Tests for CommandSimulator."""

    def test_initialization(self):
        """Test simulator initialization."""
        sim = CommandSimulator()
        assert sim.filesystem is not None
        assert sim.environment["HOME"] == "/home/user"
        assert sim.environment["USER"] == "user"
        assert len(sim.python_imports) == 0

    def test_simulate_empty_command(self):
        """Test simulating an empty command."""
        sim = CommandSimulator()
        result = sim.simulate("")
        assert result.success is True
        assert result.output == ""
        assert result.exit_code == 0

    def test_simulate_echo(self):
        """Test simulating echo command."""
        sim = CommandSimulator()
        result = sim.simulate("echo Hello World")
        assert result.success is True
        assert result.output == "Hello World"
        assert result.exit_code == 0

    def test_simulate_echo_with_quotes(self):
        """Test echo with quoted strings."""
        sim = CommandSimulator()
        result = sim.simulate('echo "Hello World"')
        assert result.success is True
        assert result.output == "Hello World"

    def test_simulate_pwd(self):
        """Test simulating pwd command."""
        sim = CommandSimulator()
        result = sim.simulate("pwd")
        assert result.success is True
        assert result.output == "/home/user"
        assert result.exit_code == 0

    def test_simulate_cd(self):
        """Test simulating cd command."""
        sim = CommandSimulator()
        sim.filesystem.create_directory("/tmp")
        result = sim.simulate("cd /tmp")
        assert result.success is True
        assert sim.filesystem.current_dir == "/tmp"

    def test_simulate_cd_nonexistent(self):
        """Test cd to nonexistent directory."""
        sim = CommandSimulator()
        result = sim.simulate("cd /nonexistent")
        assert result.success is False
        assert "No such file or directory" in result.error

    def test_simulate_mkdir(self):
        """Test simulating mkdir command."""
        sim = CommandSimulator()
        result = sim.simulate("mkdir projects")
        assert result.success is True
        assert sim.filesystem.is_directory("/home/user/projects")
        assert result.state_changes["created_directory"] == "projects"

    def test_simulate_mkdir_no_args(self):
        """Test mkdir without arguments."""
        sim = CommandSimulator()
        result = sim.simulate("mkdir")
        assert result.success is False
        assert "missing operand" in result.error

    def test_simulate_touch(self):
        """Test simulating touch command."""
        sim = CommandSimulator()
        result = sim.simulate("touch newfile.txt")
        assert result.success is True
        assert sim.filesystem.is_file("/home/user/newfile.txt")

    def test_simulate_ls(self):
        """Test simulating ls command."""
        sim = CommandSimulator()
        sim.filesystem.write_file("/home/user/file1.txt", "content")
        sim.filesystem.write_file("/home/user/file2.txt", "content")
        result = sim.simulate("ls")
        assert result.success is True
        assert "file1.txt" in result.output
        assert "file2.txt" in result.output

    def test_simulate_ls_nonexistent(self):
        """Test ls on nonexistent directory."""
        sim = CommandSimulator()
        result = sim.simulate("ls /nonexistent")
        assert result.success is False

    def test_simulate_cat(self):
        """Test simulating cat command."""
        sim = CommandSimulator()
        sim.filesystem.write_file("/home/user/test.txt", "Hello, World!")
        result = sim.simulate("cat test.txt")
        assert result.success is True
        assert result.output == "Hello, World!"

    def test_simulate_cat_nonexistent(self):
        """Test cat on nonexistent file."""
        sim = CommandSimulator()
        result = sim.simulate("cat nonexistent.txt")
        assert result.success is False

    def test_simulate_cat_no_args(self):
        """Test cat without arguments."""
        sim = CommandSimulator()
        result = sim.simulate("cat")
        assert result.success is False
        assert "missing file operand" in result.error

    def test_simulate_python_import(self):
        """Test simulating Python import."""
        sim = CommandSimulator()
        result = sim.simulate("import torch")
        assert result.success is True
        assert "torch" in sim.python_imports
        assert result.state_changes["python_import"] == "torch"

    def test_simulate_python_from_import(self):
        """Test simulating Python from import."""
        sim = CommandSimulator()
        result = sim.simulate("from numpy import array")
        assert result.success is True
        assert "numpy" in sim.python_imports

    def test_simulate_python_variable_assignment(self):
        """Test simulating Python variable assignment."""
        sim = CommandSimulator()
        result = sim.simulate("x = 42")
        assert result.success is True
        assert "x" in sim.python_variables

    def test_simulate_python_print(self):
        """Test simulating Python print statement."""
        sim = CommandSimulator()
        result = sim.simulate('print("Hello")')
        assert result.success is True
        assert result.output == "Hello"

    def test_simulate_python_command_no_args(self):
        """Test python command without arguments."""
        sim = CommandSimulator()
        result = sim.simulate("python")
        assert result.success is True
        assert "Python" in result.output

    def test_simulate_python_command_with_code(self):
        """Test python -c command."""
        sim = CommandSimulator()
        result = sim.simulate('python -c "import sys"')
        assert result.success is True
        assert "sys" in sim.python_imports

    def test_simulate_python_file_execution(self):
        """Test executing a Python file."""
        sim = CommandSimulator()
        sim.filesystem.write_file("/home/user/script.py", "import os")
        result = sim.simulate("python script.py")
        assert result.success is True
        assert "os" in sim.python_imports

    def test_simulate_python_file_nonexistent(self):
        """Test executing nonexistent Python file."""
        sim = CommandSimulator()
        result = sim.simulate("python nonexistent.py")
        assert result.success is False
        assert "No such file or directory" in result.error

    def test_simulate_pip_install(self):
        """Test simulating pip install."""
        sim = CommandSimulator()
        result = sim.simulate("pip install requests")
        assert result.success is True
        assert "Successfully installed" in result.output
        assert result.state_changes["installed_package"] == "requests"

    def test_simulate_pip_list(self):
        """Test simulating pip list."""
        sim = CommandSimulator()
        result = sim.simulate("pip list")
        assert result.success is True
        assert "pip" in result.output

    def test_simulate_pip_no_args(self):
        """Test pip without arguments."""
        sim = CommandSimulator()
        result = sim.simulate("pip")
        assert result.success is True
        assert "Usage" in result.output

    def test_simulate_pip_install_no_package(self):
        """Test pip install without package name."""
        sim = CommandSimulator()
        result = sim.simulate("pip install")
        assert result.success is False
        assert "requirement" in result.error

    def test_simulate_git_init(self):
        """Test simulating git init."""
        sim = CommandSimulator()
        result = sim.simulate("git init")
        assert result.success is True
        assert "Initialized" in result.output
        assert result.state_changes["git_initialized"] is True

    def test_simulate_git_status(self):
        """Test simulating git status."""
        sim = CommandSimulator()
        result = sim.simulate("git status")
        assert result.success is True
        assert "branch" in result.output.lower()

    def test_simulate_git_clone(self):
        """Test simulating git clone."""
        sim = CommandSimulator()
        result = sim.simulate("git clone https://github.com/user/repo.git")
        assert result.success is True
        assert "Cloning" in result.output

    def test_simulate_git_clone_no_repo(self):
        """Test git clone without repository."""
        sim = CommandSimulator()
        result = sim.simulate("git clone")
        assert result.success is False
        assert "repository" in result.error.lower()

    def test_simulate_docker_run(self):
        """Test simulating docker run."""
        sim = CommandSimulator()
        result = sim.simulate("docker run nginx")
        assert result.success is True
        assert "Running" in result.output or "nginx" in result.output

    def test_simulate_docker_ps(self):
        """Test simulating docker ps."""
        sim = CommandSimulator()
        result = sim.simulate("docker ps")
        assert result.success is True
        assert "CONTAINER" in result.output

    def test_simulate_docker_build(self):
        """Test simulating docker build."""
        sim = CommandSimulator()
        result = sim.simulate("docker build .")
        assert result.success is True
        assert result.state_changes["docker_image_built"] is True

    def test_simulate_kubectl_get(self):
        """Test simulating kubectl get."""
        sim = CommandSimulator()
        result = sim.simulate("kubectl get pods")
        assert result.success is True
        assert "NAME" in result.output or "pods" in result.output.lower()

    def test_simulate_kubectl_apply(self):
        """Test simulating kubectl apply."""
        sim = CommandSimulator()
        result = sim.simulate("kubectl apply -f deployment.yaml")
        assert result.success is True
        assert "created" in result.output.lower() or "updated" in result.output.lower()

    def test_simulate_with_llm_fallback(self):
        """Test LLM fallback for unknown command."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Success: yes\nExit Code: 0\nOutput:\nCommand executed successfully"
        )

        sim = CommandSimulator(llm_client=mock_client)
        result = sim.simulate("custom-unknown-command arg1 arg2")

        assert mock_client.generate.called
        assert result.success is True
        assert result.state_changes.get("llm_simulated") is True

    def test_simulate_unknown_without_llm(self):
        """Test unknown command without LLM client."""
        sim = CommandSimulator()  # No LLM client
        result = sim.simulate("totally-unknown-command")
        assert result.success is False
        assert result.exit_code == 127
        assert "Unknown command" in result.error

    def test_simulate_with_context(self):
        """Test simulation with learning context."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Success: yes\nExit Code: 0\nOutput:\nTensor created"
        )

        sim = CommandSimulator(llm_client=mock_client)
        context = "User is learning PyTorch tensor operations"
        sim.simulate("torch.tensor([1, 2, 3])", context=context)

        # Verify context was passed to LLM
        call_args = mock_client.generate.call_args
        assert context in call_args[1]["prompt"]

    def test_simulate_invalid_syntax(self):
        """Test command with invalid shell syntax."""
        sim = CommandSimulator()
        result = sim.simulate('echo "unclosed quote')
        assert result.success is False
        assert "Invalid command syntax" in result.error
        assert result.exit_code == 1

    def test_reset_simulator(self):
        """Test resetting simulator state."""
        sim = CommandSimulator()

        # Modify state
        sim.filesystem.write_file("/home/user/test.txt", "content")
        sim.simulate("import numpy")
        sim.simulate("x = 10")
        sim.filesystem.current_dir = "/tmp"

        # Reset
        sim.reset()

        # Verify state is reset
        assert not sim.filesystem.exists("/home/user/test.txt")
        assert len(sim.python_imports) == 0
        assert len(sim.python_variables) == 0
        assert sim.filesystem.current_dir == "/home/user"
        assert sim.environment["HOME"] == "/home/user"

    def test_multiple_commands_preserve_state(self):
        """Test that state is preserved across multiple commands."""
        sim = CommandSimulator()

        # Create file and directory
        sim.simulate("mkdir projects")
        sim.simulate("touch projects/readme.md")

        # Verify state persisted
        assert sim.filesystem.is_directory("/home/user/projects")
        assert sim.filesystem.is_file("/home/user/projects/readme.md")

        # Navigate and list
        sim.simulate("cd projects")
        result = sim.simulate("ls")
        assert "readme.md" in result.output

    def test_python_imports_accumulate(self):
        """Test that Python imports accumulate over session."""
        sim = CommandSimulator()

        sim.simulate("import torch")
        sim.simulate("import numpy")
        sim.simulate("from pandas import DataFrame")

        assert "torch" in sim.python_imports
        assert "numpy" in sim.python_imports
        assert "pandas" in sim.python_imports
        assert len(sim.python_imports) == 3

    def test_llm_fallback_error_handling(self):
        """Test error handling in LLM fallback."""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")

        sim = CommandSimulator(llm_client=mock_client)
        result = sim.simulate("unknown-command")

        assert result.success is False
        assert "Simulation error" in result.error

    @pytest.mark.integration
    def test_integration_with_real_llm(self):
        """Integration test with real LLM client (requires API key)."""
        # This test is skipped by default (requires API key)
        # To run: pytest -m integration
        pytest.skip("Integration test - requires API key")
