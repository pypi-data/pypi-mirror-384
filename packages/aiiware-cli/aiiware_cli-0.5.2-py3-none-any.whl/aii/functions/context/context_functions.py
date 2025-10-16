"""Context Functions - Fundamental data gathering functions"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)


class GitContextFunction(FunctionPlugin):
    """Get git repository context information"""

    @property
    def name(self) -> str:
        return "get_git_context"

    @property
    def description(self) -> str:
        return (
            "Get LOCAL git repository information including latest commit, status, and branch info. "
            "This function reads the local .git directory. "
            "NOT for GitHub API operations - for GitHub repositories/issues/PRs, use mcp_tool instead."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "info_type": ParameterSchema(
                name="info_type",
                type="string",
                required=False,
                default="latest_commit",
                choices=["latest_commit", "status", "branch", "history", "all"],
                description="Type of git information to retrieve",
            ),
            "count": ParameterSchema(
                name="count",
                type="integer",
                required=False,
                default=1,
                description="Number of commits to retrieve (for history)",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: result + metrics"""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if we're in a git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                cwd=context.config.get("working_dir", "."),
            )
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Not in a git repository"])
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(
                valid=False, errors=[f"Git not available: {str(e)}"]
            )

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute git context retrieval"""
        try:
            info_type = parameters.get("info_type", "latest_commit")
            count = parameters.get("count", 1)
            working_dir = context.config.get("working_dir", ".")

            git_data: dict[str, Any] = {}

            if info_type in ["latest_commit", "all"]:
                git_data["latest_commit"] = await self._get_latest_commit(working_dir)

            if info_type in ["status", "all"]:
                git_data["status"] = await self._get_git_status(working_dir)

            if info_type in ["branch", "all"]:
                git_data["branch"] = await self._get_branch_info(working_dir)

            if info_type in ["history", "all"]:
                git_data["history"] = await self._get_commit_history(working_dir, count)

            return ExecutionResult(
                success=True,
                message=f"Retrieved git {info_type} information",
                data={
                    "git_context": git_data,
                    "info_type": info_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Failed to get git context: {str(e)}"
            )

    async def _get_latest_commit(self, working_dir: str) -> dict[str, str]:
        """Get latest commit information"""
        try:
            # Get commit message and details
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%H|%s|%b|%an|%ad"],
                capture_output=True,
                text=True,
                cwd=working_dir,
            )

            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split("|", 4)
                return {
                    "hash": parts[0] if len(parts) > 0 else "",
                    "subject": parts[1] if len(parts) > 1 else "",
                    "body": parts[2] if len(parts) > 2 else "",
                    "author": parts[3] if len(parts) > 3 else "",
                    "date": parts[4] if len(parts) > 4 else "",
                    "full_message": (
                        parts[1] + ("\n\n" + parts[2] if parts[2] else "")
                        if len(parts) > 1
                        else ""
                    ),
                }
            return {"error": "No commits found"}
        except Exception as e:
            return {"error": f"Failed to get latest commit: {str(e)}"}

    async def _get_git_status(self, working_dir: str) -> dict[str, Any]:
        """Get git status information"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=working_dir,
            )

            if result.returncode == 0:
                status_lines = (
                    result.stdout.strip().split("\n") if result.stdout.strip() else []
                )

                staged = []
                modified = []
                untracked = []

                for line in status_lines:
                    if not line:
                        continue
                    status_code = line[:2]
                    filename = line[3:]

                    if status_code[0] in ["A", "M", "D", "R", "C"]:
                        staged.append({"file": filename, "status": status_code[0]})
                    if status_code[1] in ["M", "D"]:
                        modified.append({"file": filename, "status": status_code[1]})
                    if status_code == "??":
                        untracked.append(filename)

                return {
                    "staged": staged,
                    "modified": modified,
                    "untracked": untracked,
                    "clean": len(status_lines) == 0,
                }

            return {"error": "Failed to get git status"}
        except Exception as e:
            return {"error": f"Failed to get git status: {str(e)}"}

    async def _get_branch_info(self, working_dir: str) -> dict[str, str]:
        """Get git branch information"""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=working_dir,
            )

            current_branch = (
                result.stdout.strip() if result.returncode == 0 else "unknown"
            )

            return {
                "current_branch": current_branch,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": f"Failed to get branch info: {str(e)}"}

    async def _get_commit_history(
        self, working_dir: str, count: int
    ) -> list[dict[str, str]]:
        """Get commit history"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H|%s|%an|%ad"],
                capture_output=True,
                text=True,
                cwd=working_dir,
            )

            if result.returncode == 0 and result.stdout.strip():
                commits = []
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("|", 3)
                    if len(parts) >= 4:
                        commits.append(
                            {
                                "hash": parts[0],
                                "subject": parts[1],
                                "author": parts[2],
                                "date": parts[3],
                            }
                        )
                return commits

            return []
        except Exception as e:
            return [{"error": f"Failed to get commit history: {str(e)}"}]


class FileContextFunction(FunctionPlugin):
    """Get file system context information"""

    @property
    def name(self) -> str:
        return "get_file_context"

    @property
    def description(self) -> str:
        return "Get file system metadata and structure (NOT for reading file contents - use MCP tools for that). Use info_type='structure' for directory listing, 'stats' for file metadata. For reading actual file contents, use MCP's read_text_file tool instead."

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "path": ParameterSchema(
                name="path",
                type="string",
                required=False,
                default=".",
                description="Path to analyze (file or directory)",
            ),
            "info_type": ParameterSchema(
                name="info_type",
                type="string",
                required=False,
                default="structure",
                choices=["structure", "stats", "all"],
                description="Type of file information to retrieve: 'structure' for directory listing, 'stats' for file metadata, 'all' for both. NOTE: For reading file CONTENTS, use MCP's read_text_file tool instead.",
            ),
            "max_files": ParameterSchema(
                name="max_files",
                type="integer",
                required=False,
                default=20,
                description="Maximum number of files to analyze",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> "OutputMode":
        """Default to CLEAN mode - just show the content/structure"""
        from aii.core.models import OutputMode
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list["OutputMode"]:
        """Support all output modes"""
        from aii.core.models import OutputMode
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Always valid for file operations"""
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute file context retrieval"""
        try:
            path = parameters.get("path", ".")
            info_type = parameters.get("info_type", "structure")
            max_files = parameters.get("max_files", 20)

            # Resolve path relative to working directory
            working_dir = context.config.get("working_dir", ".")
            full_path = Path(working_dir) / path

            if not full_path.exists():
                return ExecutionResult(
                    success=False, message=f"Path does not exist: {path}"
                )

            file_data = {}

            if info_type in ["structure", "all"]:
                file_data["structure"] = await self._get_directory_structure(
                    full_path, max_files
                )

            if info_type in ["stats", "all"]:
                file_data["stats"] = await self._get_path_stats(full_path)

            # Format clean output based on what was retrieved
            clean_output = self._format_clean_output(file_data, full_path, info_type)

            return ExecutionResult(
                success=True,
                message=f"Retrieved file context for {path}",
                data={
                    "file_context": file_data,
                    "path": str(path),
                    "info_type": info_type,
                    "timestamp": datetime.now().isoformat(),
                    "clean_output": clean_output,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Failed to get file context: {str(e)}"
            )

    async def _get_directory_structure(
        self, path: Path, max_files: int
    ) -> dict[str, Any]:
        """Get directory structure"""
        try:
            if path.is_file():
                return {"type": "file", "name": path.name, "size": path.stat().st_size}

            structure: dict[str, Any] = {
                "type": "directory",
                "name": path.name,
                "files": [],
                "directories": [],
            }

            count = 0
            for item in sorted(path.iterdir()):
                if count >= max_files:
                    structure["truncated"] = True
                    break

                if item.is_file():
                    structure["files"].append(
                        {
                            "name": item.name,
                            "size": item.stat().st_size,
                            "extension": item.suffix,
                        }
                    )
                elif item.is_dir() and not item.name.startswith("."):
                    structure["directories"].append(item.name)

                count += 1

            return structure
        except Exception as e:
            return {"error": f"Failed to get directory structure: {str(e)}"}

    async def _get_file_content(self, path: Path) -> dict[str, Any]:
        """
        DEPRECATED: Use MCP's read_text_file tool instead.
        This method is kept for backward compatibility but returns an error.
        """
        return {
            "error": "Reading file contents via get_file_context is deprecated. Use MCP's read_text_file tool instead."
        }

    async def _get_file_content_legacy(self, path: Path) -> dict[str, Any]:
        """Legacy file content reading (DEPRECATED - kept for reference only)"""
        try:
            MAX_SIZE = 100000  # 100KB limit (increased for better usability)

            if path.stat().st_size > MAX_SIZE:
                return {
                    "error": f"File too large ({path.stat().st_size} bytes, max {MAX_SIZE})",
                    "size": path.stat().st_size,
                }

            with open(path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return {
                "content": content,
                "size": len(content),
                "lines": len(content.split("\n")),
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    async def _get_path_stats(self, path: Path) -> dict[str, Any]:
        """Get path statistics"""
        try:
            stats = path.stat()
            return {
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "name": path.name,
                "extension": path.suffix if path.is_file() else None,
            }
        except Exception as e:
            return {"error": f"Failed to get path stats: {str(e)}"}

    def _format_clean_output(
        self, file_data: dict[str, Any], path: Path, info_type: str
    ) -> str:
        """Format clean output for display (metadata only - use MCP for file contents)"""
        output_parts = []

        # Show structure if requested
        if "structure" in file_data:
            structure = file_data["structure"]
            if structure.get("type") == "file":
                output_parts.append(
                    f"File: {structure['name']} ({structure['size']} bytes)"
                )
            elif structure.get("type") == "directory":
                output_parts.append(f"Directory: {structure.get('name', path.name)}")
                if structure.get("files"):
                    output_parts.append(f"\nFiles ({len(structure['files'])}):")
                    for f in structure["files"][:10]:  # Show first 10
                        output_parts.append(f"  - {f['name']} ({f['size']} bytes)")
                    if len(structure["files"]) > 10:
                        output_parts.append(f"  ... and {len(structure['files']) - 10} more")
                if structure.get("directories"):
                    output_parts.append(f"\nDirectories ({len(structure['directories'])}):")
                    for d in structure["directories"][:10]:
                        output_parts.append(f"  - {d}/")
                    if len(structure["directories"]) > 10:
                        output_parts.append(
                            f"  ... and {len(structure['directories']) - 10} more"
                        )

        # Show stats if requested and nothing else shown
        elif "stats" in file_data:
            stats = file_data["stats"]
            if "error" not in stats:
                output_parts.append(f"Path: {stats['name']}")
                output_parts.append(f"Type: {'File' if stats['is_file'] else 'Directory'}")
                output_parts.append(f"Size: {stats['size']} bytes")
                output_parts.append(f"Modified: {stats['modified']}")

        return "\n".join(output_parts) if output_parts else "No data retrieved"


class SystemContextFunction(FunctionPlugin):
    """Get system context information"""

    @property
    def name(self) -> str:
        return "get_system_context"

    @property
    def description(self) -> str:
        return "Get system information including environment, process info, and working directory"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "info_type": ParameterSchema(
                name="info_type",
                type="string",
                required=False,
                default="environment",
                choices=["environment", "working_dir", "process", "all"],
                description="Type of system information to retrieve",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Always valid for system operations"""
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute system context retrieval"""
        try:
            info_type = parameters.get("info_type", "environment")

            system_data = {}

            if info_type in ["environment", "all"]:
                system_data["environment"] = await self._get_environment_info()

            if info_type in ["working_dir", "all"]:
                system_data["working_dir"] = await self._get_working_directory_info(
                    context
                )

            if info_type in ["process", "all"]:
                system_data["process"] = await self._get_process_info()

            return ExecutionResult(
                success=True,
                message=f"Retrieved system {info_type} information",
                data={
                    "system_context": system_data,
                    "info_type": info_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Failed to get system context: {str(e)}"
            )

    async def _get_environment_info(self) -> dict[str, Any]:
        """Get environment information"""
        try:
            return {
                "platform": os.name,
                "cwd": os.getcwd(),
                "user": os.environ.get("USER") or os.environ.get("USERNAME", "unknown"),
                "home": os.environ.get("HOME")
                or os.environ.get("USERPROFILE", "unknown"),
                "path": os.environ.get("PATH", "").split(os.pathsep)[
                    :5
                ],  # First 5 PATH entries
            }
        except Exception as e:
            return {"error": f"Failed to get environment info: {str(e)}"}

    async def _get_working_directory_info(
        self, context: ExecutionContext
    ) -> dict[str, Any]:
        """Get working directory information"""
        try:
            working_dir = context.config.get("working_dir", os.getcwd())
            path = Path(working_dir)

            return {
                "current_directory": str(path),
                "exists": path.exists(),
                "is_git_repo": (path / ".git").exists(),
                "parent": str(path.parent),
                "name": path.name,
            }
        except Exception as e:
            return {"error": f"Failed to get working directory info: {str(e)}"}

    async def _get_process_info(self) -> dict[str, Any]:
        """Get current process information"""
        try:
            import psutil

            process = psutil.Process()

            return {
                "pid": process.pid,
                "name": process.name(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": process.memory_info()._asdict(),
                "create_time": datetime.fromtimestamp(
                    process.create_time()
                ).isoformat(),
            }
        except ImportError:
            return {"error": "psutil not available for process info"}
        except Exception as e:
            return {"error": f"Failed to get process info: {str(e)}"}
