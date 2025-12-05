"""
Command and file system simulator for safe learning environments.

This module provides simulation of command execution and file system operations
without actually running commands or modifying the real file system.
"""

import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from skillforge.utils.llm_client import BaseLLMClient


@dataclass
class SimulationResult:
    """Result of a command simulation.

    Attributes:
        success: Whether the command executed successfully
        output: Standard output from the command
        error: Error message if command failed
        exit_code: Exit code (0 for success, non-zero for failure)
        state_changes: Dictionary of state changes (files, env vars, etc.)
    """

    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    state_changes: dict[str, Any] = field(default_factory=dict)


class VirtualFileSystem:
    """Simulated file system for safe command execution.

    Maintains an in-memory representation of files and directories
    without touching the actual file system.
    """

    def __init__(self) -> None:
        """Initialize the virtual file system."""
        self.files: dict[str, str] = {}
        self.directories: set[str] = {"/", "/home", "/home/user", "/tmp"}
        self.current_dir = "/home/user"

    def normalize_path(self, path: str) -> str:
        """Normalize a path to absolute form.

        Args:
            path: Path to normalize (can be relative or absolute)

        Returns:
            Absolute normalized path
        """
        if not path.startswith("/"):
            # Relative path - make it absolute
            if self.current_dir == "/":
                path = f"/{path}"
            else:
                path = f"{self.current_dir}/{path}"

        # Normalize (remove ./ and ../)
        parts: list[str] = []
        for part in path.split("/"):
            if part == "..":
                if parts:
                    parts.pop()
            elif part and part != ".":
                parts.append(part)

        return "/" + "/".join(parts) if parts else "/"

    def exists(self, path: str) -> bool:
        """Check if a path exists.

        Args:
            path: Path to check

        Returns:
            True if path exists (as file or directory)
        """
        norm_path = self.normalize_path(path)
        return norm_path in self.files or norm_path in self.directories

    def is_file(self, path: str) -> bool:
        """Check if path is a file.

        Args:
            path: Path to check

        Returns:
            True if path exists and is a file
        """
        return self.normalize_path(path) in self.files

    def is_directory(self, path: str) -> bool:
        """Check if path is a directory.

        Args:
            path: Path to check

        Returns:
            True if path exists and is a directory
        """
        return self.normalize_path(path) in self.directories

    def read_file(self, path: str) -> str:
        """Read contents of a file.

        Args:
            path: Path to file

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        norm_path = self.normalize_path(path)
        if norm_path not in self.files:
            raise FileNotFoundError(f"No such file: {path}")
        return self.files[norm_path]

    def write_file(self, path: str, content: str) -> None:
        """Write content to a file.

        Args:
            path: Path to file
            content: Content to write
        """
        norm_path = self.normalize_path(path)
        # Create parent directory if needed
        parent = str(Path(norm_path).parent)
        if parent and parent not in self.directories:
            self.directories.add(parent)
        self.files[norm_path] = content

    def list_directory(self, path: str = ".") -> list[str]:
        """List contents of a directory.

        Args:
            path: Path to directory

        Returns:
            List of filenames/directory names in the directory

        Raises:
            FileNotFoundError: If directory doesn't exist
            NotADirectoryError: If path is not a directory
        """
        norm_path = self.normalize_path(path)

        if not self.exists(norm_path):
            raise FileNotFoundError(f"No such directory: {path}")

        if not self.is_directory(norm_path):
            raise NotADirectoryError(f"Not a directory: {path}")

        # Find all direct children
        results = []
        prefix = norm_path if norm_path.endswith("/") else norm_path + "/"
        if norm_path == "/":
            prefix = "/"

        # Check files
        for file_path in self.files:
            if file_path.startswith(prefix):
                remainder = file_path[len(prefix) :]
                if "/" not in remainder:  # Direct child
                    results.append(remainder)

        # Check directories
        for dir_path in self.directories:
            if dir_path != norm_path and dir_path.startswith(prefix):
                remainder = dir_path[len(prefix) :]
                if "/" not in remainder:  # Direct child
                    results.append(remainder)

        return sorted(results)

    def create_directory(self, path: str) -> None:
        """Create a directory.

        Args:
            path: Path to directory to create
        """
        norm_path = self.normalize_path(path)
        self.directories.add(norm_path)

        # Also create parent directories
        parent = str(Path(norm_path).parent)
        while parent and parent not in self.directories and parent != "/":
            self.directories.add(parent)
            parent = str(Path(parent).parent)

    def touch(self, path: str) -> None:
        """Create an empty file or update its timestamp.

        Args:
            path: Path to file
        """
        norm_path = self.normalize_path(path)
        if norm_path not in self.files:
            self.write_file(path, "")


class CommandSimulator:
    """Simulates command execution for learning environments.

    Provides pattern-based simulation for common commands with fallback
    to LLM for unknown commands.
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None) -> None:
        """Initialize the command simulator.

        Args:
            llm_client: LLM client for fallback simulation of unknown commands
        """
        self.llm_client = llm_client
        self.filesystem = VirtualFileSystem()
        self.environment: dict[str, str] = {
            "HOME": "/home/user",
            "USER": "user",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }
        self.python_imports: set[str] = set()
        self.python_variables: dict[str, Any] = {}

    def simulate(self, command: str, context: Optional[str] = None) -> SimulationResult:
        """Simulate execution of a command.

        Args:
            command: Command to simulate
            context: Optional context about the learning exercise

        Returns:
            SimulationResult with output and state changes
        """
        command = command.strip()
        if not command:
            return SimulationResult(
                success=True, output="", exit_code=0, state_changes={}
            )

        # Try to parse the command
        try:
            parts = shlex.split(command)
        except ValueError:
            # Invalid syntax
            return SimulationResult(
                success=False,
                output="",
                error=f"Invalid command syntax: {command}",
                exit_code=1,
            )

        if not parts:
            return SimulationResult(
                success=True, output="", exit_code=0, state_changes={}
            )

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Check for known command patterns
        if cmd == "echo":
            return self._simulate_echo(args)
        elif cmd == "ls":
            return self._simulate_ls(args)
        elif cmd == "cat":
            return self._simulate_cat(args)
        elif cmd == "mkdir":
            return self._simulate_mkdir(args)
        elif cmd == "touch":
            return self._simulate_touch(args)
        elif cmd == "cd":
            return self._simulate_cd(args)
        elif cmd == "pwd":
            return self._simulate_pwd()
        elif cmd == "python" or cmd == "python3":
            return self._simulate_python_command(args, context)
        elif cmd == "pip" or cmd == "pip3":
            return self._simulate_pip(args)
        elif cmd == "git":
            return self._simulate_git(args)
        elif cmd == "docker":
            return self._simulate_docker(args)
        elif cmd == "kubectl":
            return self._simulate_kubectl(args)
        else:
            # Check if it's a Python statement
            if self._is_python_code(command):
                return self._simulate_python_code(command, context)
            # Unknown command - use LLM fallback
            return self._simulate_with_llm(command, context)

    def _simulate_echo(self, args: list[str]) -> SimulationResult:
        """Simulate echo command."""
        output = " ".join(args)
        return SimulationResult(success=True, output=output, exit_code=0)

    def _simulate_ls(self, args: list[str]) -> SimulationResult:
        """Simulate ls command."""
        path = args[0] if args else "."
        try:
            files = self.filesystem.list_directory(path)
            output = "\n".join(files) if files else ""
            return SimulationResult(success=True, output=output, exit_code=0)
        except (FileNotFoundError, NotADirectoryError) as e:
            return SimulationResult(success=False, output="", error=str(e), exit_code=1)

    def _simulate_cat(self, args: list[str]) -> SimulationResult:
        """Simulate cat command."""
        if not args:
            return SimulationResult(
                success=False, output="", error="cat: missing file operand", exit_code=1
            )

        path = args[0]
        try:
            content = self.filesystem.read_file(path)
            return SimulationResult(success=True, output=content, exit_code=0)
        except FileNotFoundError as e:
            return SimulationResult(success=False, output="", error=str(e), exit_code=1)

    def _simulate_mkdir(self, args: list[str]) -> SimulationResult:
        """Simulate mkdir command."""
        if not args:
            return SimulationResult(
                success=False,
                output="",
                error="mkdir: missing operand",
                exit_code=1,
            )

        path = args[0]
        self.filesystem.create_directory(path)
        return SimulationResult(
            success=True,
            output="",
            exit_code=0,
            state_changes={"created_directory": path},
        )

    def _simulate_touch(self, args: list[str]) -> SimulationResult:
        """Simulate touch command."""
        if not args:
            return SimulationResult(
                success=False,
                output="",
                error="touch: missing file operand",
                exit_code=1,
            )

        path = args[0]
        self.filesystem.touch(path)
        return SimulationResult(
            success=True, output="", exit_code=0, state_changes={"created_file": path}
        )

    def _simulate_cd(self, args: list[str]) -> SimulationResult:
        """Simulate cd command."""
        if not args:
            # cd with no args goes to home
            self.filesystem.current_dir = self.environment.get("HOME", "/home/user")
            return SimulationResult(success=True, output="", exit_code=0)

        path = args[0]
        norm_path = self.filesystem.normalize_path(path)

        if not self.filesystem.is_directory(norm_path):
            return SimulationResult(
                success=False,
                output="",
                error=f"cd: {path}: No such file or directory",
                exit_code=1,
            )

        self.filesystem.current_dir = norm_path
        return SimulationResult(
            success=True,
            output="",
            exit_code=0,
            state_changes={"current_directory": norm_path},
        )

    def _simulate_pwd(self) -> SimulationResult:
        """Simulate pwd command."""
        return SimulationResult(
            success=True, output=self.filesystem.current_dir, exit_code=0
        )

    def _simulate_python_command(
        self, args: list[str], context: Optional[str]
    ) -> SimulationResult:
        """Simulate python command execution."""
        if not args:
            return SimulationResult(
                success=True,
                output="Python 3.9.0\nType 'help' for more information.",
                exit_code=0,
            )

        if args[0] == "-c" and len(args) > 1:
            # Execute Python code
            code = args[1]
            return self._simulate_python_code(code, context)
        elif args[0].endswith(".py"):
            # Execute Python file
            filename = args[0]
            try:
                code = self.filesystem.read_file(filename)
                return self._simulate_python_code(code, context)
            except FileNotFoundError:
                return SimulationResult(
                    success=False,
                    output="",
                    error=f"python: can't open file '{filename}': "
                    "[Errno 2] No such file or directory",
                    exit_code=2,
                )
        else:
            # Unknown python option
            return self._simulate_with_llm(f"python {' '.join(args)}", context)

    def _is_python_code(self, command: str) -> bool:
        """Check if command looks like Python code."""
        python_patterns = [
            r"^import\s+\w+",
            r"^from\s+\w+\s+import",
            r"^\w+\s*=\s*.+",
            r"^print\(",
            r"^def\s+\w+\(",
            r"^class\s+\w+",
        ]
        return any(re.match(pattern, command) for pattern in python_patterns)

    def _simulate_python_code(
        self, code: str, context: Optional[str]
    ) -> SimulationResult:
        """Simulate Python code execution."""
        code = code.strip()

        # Handle imports
        if code.startswith("import ") or code.startswith("from "):
            return self._simulate_python_import(code)

        # Handle simple print statements
        print_match = re.match(r'print\(["\'](.+?)["\']\)', code)
        if print_match:
            output = print_match.group(1)
            return SimulationResult(success=True, output=output, exit_code=0)

        # Handle simple variable assignments
        assign_match = re.match(r"(\w+)\s*=\s*(.+)", code)
        if assign_match:
            var_name = assign_match.group(1)
            var_value = assign_match.group(2)
            self.python_variables[var_name] = var_value
            return SimulationResult(
                success=True,
                output="",
                exit_code=0,
                state_changes={"python_variable": var_name},
            )

        # For more complex code, use LLM fallback
        return self._simulate_with_llm(code, context)

    def _simulate_python_import(self, code: str) -> SimulationResult:
        """Simulate Python import statement."""
        # Extract module name
        if code.startswith("import "):
            module = code.replace("import ", "").split()[0].split(".")[0]
        elif code.startswith("from "):
            module = code.split()[1].split(".")[0]
        else:
            return SimulationResult(
                success=False, output="", error="Invalid import syntax", exit_code=1
            )

        self.python_imports.add(module)
        return SimulationResult(
            success=True,
            output="",
            exit_code=0,
            state_changes={"python_import": module},
        )

    def _simulate_pip(self, args: list[str]) -> SimulationResult:
        """Simulate pip command."""
        if not args:
            return SimulationResult(
                success=True,
                output="Usage: pip <command> [options]\n\n"
                "Commands:\n  install   Install packages\n"
                "  list      List installed packages",
                exit_code=0,
            )

        cmd = args[0]
        if cmd == "install":
            if len(args) < 2:
                return SimulationResult(
                    success=False,
                    output="",
                    error="ERROR: You must give at least one requirement to install",
                    exit_code=1,
                )
            package = args[1]
            return SimulationResult(
                success=True,
                output=f"Successfully installed {package}",
                exit_code=0,
                state_changes={"installed_package": package},
            )
        elif cmd == "list":
            return SimulationResult(
                success=True,
                output="Package    Version\n---------- -------\npip        24.0",
                exit_code=0,
            )
        else:
            return SimulationResult(
                success=False,
                output="",
                error=f"ERROR: unknown command '{cmd}'",
                exit_code=1,
            )

    def _simulate_git(self, args: list[str]) -> SimulationResult:
        """Simulate git command."""
        if not args:
            return SimulationResult(
                success=True,
                output="usage: git [--version] [--help] <command> [<args>]",
                exit_code=0,
            )

        cmd = args[0]
        if cmd == "init":
            return SimulationResult(
                success=True,
                output="Initialized empty Git repository in .git/",
                exit_code=0,
                state_changes={"git_initialized": True},
            )
        elif cmd == "status":
            return SimulationResult(
                success=True,
                output="On branch main\nnothing to commit, working tree clean",
                exit_code=0,
            )
        elif cmd == "clone":
            if len(args) < 2:
                return SimulationResult(
                    success=False,
                    output="",
                    error="fatal: You must specify a repository to clone.",
                    exit_code=128,
                )
            repo = args[1]
            return SimulationResult(
                success=True,
                output=f"Cloning into '{repo.split('/')[-1].replace('.git', '')}'...",
                exit_code=0,
                state_changes={"git_cloned": repo},
            )
        else:
            # Other git commands - use generic response or LLM
            return SimulationResult(
                success=True, output=f"git {cmd} completed successfully", exit_code=0
            )

    def _simulate_docker(self, args: list[str]) -> SimulationResult:
        """Simulate docker command."""
        if not args:
            return SimulationResult(
                success=True,
                output="Usage: docker [OPTIONS] COMMAND\n\n"
                "A self-sufficient runtime for containers",
                exit_code=0,
            )

        cmd = args[0]
        if cmd == "run":
            image = args[-1] if len(args) > 1 else "image"
            return SimulationResult(
                success=True,
                output=f"Running container from {image}...",
                exit_code=0,
                state_changes={"docker_container_started": image},
            )
        elif cmd == "ps":
            return SimulationResult(
                success=True,
                output="CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS",
                exit_code=0,
            )
        elif cmd == "build":
            return SimulationResult(
                success=True,
                output="Successfully built docker image",
                exit_code=0,
                state_changes={"docker_image_built": True},
            )
        else:
            return SimulationResult(
                success=True,
                output=f"docker {cmd} completed successfully",
                exit_code=0,
            )

    def _simulate_kubectl(self, args: list[str]) -> SimulationResult:
        """Simulate kubectl command."""
        if not args:
            return SimulationResult(
                success=True,
                output="kubectl controls the Kubernetes cluster manager.",
                exit_code=0,
            )

        cmd = args[0]
        if cmd == "get":
            resource = args[1] if len(args) > 1 else "pods"
            return SimulationResult(
                success=True,
                output=f"NAME                READY   STATUS    RESTARTS   AGE\n"
                f"{resource}-sample   1/1     Running   0          10s",
                exit_code=0,
            )
        elif cmd == "apply":
            return SimulationResult(
                success=True,
                output="resource created/updated successfully",
                exit_code=0,
            )
        else:
            return SimulationResult(
                success=True,
                output=f"kubectl {cmd} completed successfully",
                exit_code=0,
            )

    def _simulate_with_llm(
        self, command: str, context: Optional[str]
    ) -> SimulationResult:
        """Use LLM to simulate unknown command.

        Args:
            command: Command to simulate
            context: Optional context about the learning exercise

        Returns:
            SimulationResult from LLM simulation
        """
        if not self.llm_client:
            return SimulationResult(
                success=False,
                output="",
                error=f"Unknown command: {command}",
                exit_code=127,
            )

        # Build prompt for LLM
        prompt = f"""Simulate the output of this command in a learning environment:

Command: {command}

"""
        if context:
            prompt += f"Context: {context}\n\n"

        prompt += (
            """Provide a realistic but safe simulation of what """
            """this command would output.
Keep the output concise and educational.

Respond in the following format:
Success: [yes/no]
Exit Code: [number]
Output:
[command output here]
"""
        )

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are simulating command execution in a safe "
                "learning environment. Provide realistic but safe outputs.",
                temperature=0.3,
                max_tokens=512,
            )

            # Parse response
            success = "Success: yes" in response
            exit_code = 0 if success else 1

            # Extract output
            if "Output:" in response:
                output = response.split("Output:")[1].strip()
            else:
                output = response

            return SimulationResult(
                success=success,
                output=output,
                exit_code=exit_code,
                state_changes={"llm_simulated": True},
            )

        except Exception as e:
            return SimulationResult(
                success=False,
                output="",
                error=f"Simulation error: {str(e)}",
                exit_code=1,
            )

    def reset(self) -> None:
        """Reset simulator state to initial conditions."""
        self.filesystem = VirtualFileSystem()
        self.environment = {
            "HOME": "/home/user",
            "USER": "user",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }
        self.python_imports = set()
        self.python_variables = {}
