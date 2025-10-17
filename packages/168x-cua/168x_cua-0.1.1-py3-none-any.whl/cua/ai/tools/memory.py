import logging

from sqlalchemy import select, update

logger = logging.getLogger(__name__)

from pydantic import BaseModel
from typing import Literal

from anthropic.lib.tools import BetaAbstractMemoryTool
from anthropic.types.beta import (
    BetaMessageParam,
    BetaContentBlockParam,
    BetaMemoryTool20250818Command,
    BetaContextManagementConfigParam,
    BetaMemoryTool20250818ViewCommand,
    BetaMemoryTool20250818CreateCommand,
    BetaMemoryTool20250818DeleteCommand,
    BetaMemoryTool20250818InsertCommand,
    BetaMemoryTool20250818RenameCommand,
    BetaMemoryTool20250818StrReplaceCommand,
)

from cua.ai.tool_box import Tool, ToolResult
from server.core.database import get_db_rls_bypass
from server.core.models import DB_AgentLoop
    

class MemoryTool(Tool):
    def __init__(self, agent_loop_id: int):
        super().__init__(
            name="memory",
            description="None",
            input_model=BetaMemoryTool20250818Command,
        )
        
        self._agent_loop_id = agent_loop_id
        
        # key: path, value: memory_text
        self._data: dict[str, str] = {}


    async def __call__(self, args: BetaMemoryTool20250818Command) -> ToolResult:
        await self._load()
        
        if args.command == "view":
            result = self.view(args)
            return result # return early to avoid saving
        elif args.command == "create":
            result = self.create(args)
        elif args.command == "str_replace":
            result = self.str_replace(args)
        elif args.command == "insert":
            result = self.insert(args)
        elif args.command == "delete":
            result = self.delete(args)
        elif args.command == "rename":
            result = self.rename(args)
        else:
            raise NotImplementedError(f"Unknown command: {args.command}")
        
        await self._save()

        return result


    async def _load(self):
        async with get_db_rls_bypass() as session:
            result = await session.execute(select(DB_AgentLoop.memory).where(DB_AgentLoop.id == self._agent_loop_id))
            memory = result.scalar_one_or_none()
            if memory:
                self._data = memory
            else:
                self._data = {}
    
    
    async def _save(self):
        async with get_db_rls_bypass() as session:
            await session.execute(update(DB_AgentLoop).where(DB_AgentLoop.id == self._agent_loop_id).values(memory=self._data))
            await session.commit()


    def _validate_path(self, path: str):
        if not path.startswith("/memories"):
            raise ValueError(f"Path must start with /memories, got: {path}")
        
        return path


    def view(self, args: BetaMemoryTool20250818ViewCommand) -> ToolResult:
        path_cleaned = self._validate_path(args.path)
        
        is_file = None
        
        if path_cleaned in self._data:
            is_file = True
        else:
            for key in self._data.keys():
                if key.startswith(path_cleaned + "/"):
                    is_file = False
                    break
        
        # Special case: /memories root should always be viewable as a directory
        if is_file is None and path_cleaned == "/memories":
            is_file = False
        
        if is_file is None:
            raise RuntimeError(f"Path not found: {args.path}")
        
        if is_file:
            # Handle file viewing with line numbers
            try:
                content = self._data.get(path_cleaned, "")
                lines = content.splitlines()
                view_range = args.view_range
                
                if view_range:
                    start_line = max(1, view_range[0]) - 1
                    end_line = len(lines) if view_range[1] == -1 else view_range[1]
                    lines = lines[start_line:end_line]
                    start_num = start_line + 1
                else:
                    start_num = 1
                
                numbered_lines = [f"{i + start_num:4d}: {line}" for i, line in enumerate(lines)]
                return ToolResult(text="\n".join(numbered_lines))
            except Exception as e:
                raise RuntimeError(f"Cannot read file {args.path}: {e}") from e
        else:
            # Handle directory listing
            items: list[str] = []
            seen_items: set[str] = set()
            
            try:
                # Find all items that are children of this directory
                prefix = path_cleaned + "/"
                for key in sorted(self._data.keys()):
                    if key.startswith(prefix):
                        # Get the relative path after the directory
                        relative = key[len(prefix):]
                        # Get just the immediate child (first path component)
                        parts = relative.split("/", 1)
                        immediate_child = parts[0]
                        
                        if immediate_child and immediate_child not in seen_items:
                            seen_items.add(immediate_child)
                            # Check if this is a directory (has further descendants) or a file
                            child_path = f"{prefix}{immediate_child}"
                            is_directory = len(parts) > 1 or any(
                                k.startswith(child_path + "/") for k in self._data.keys()
                            )
                            items.append(f"{immediate_child}/" if is_directory else immediate_child)
                
                result = f"Directory: {args.path}"
                if items:
                    result += "\n" + "\n".join([f"- {item}" for item in items])
                return ToolResult(text=result)
            except Exception as e:
                raise RuntimeError(f"Cannot read directory {args.path}: {e}") from e
    
    
    def create(self, args: BetaMemoryTool20250818CreateCommand) -> ToolResult:
        path_cleaned = self._validate_path(args.path)
        
        # In a dictionary-based system, parent directories are implicit
        # Just store the file content
        self._data[path_cleaned] = args.file_text
        
        return ToolResult(text=f"File created successfully at {args.path}")
    
    
    def str_replace(self, args: BetaMemoryTool20250818StrReplaceCommand) -> ToolResult:
        path_cleaned = self._validate_path(args.path)
        
        # Check if file exists
        if path_cleaned not in self._data:
            raise FileNotFoundError(f"File not found: {args.path}")
        
        content = self._data[path_cleaned]
        
        # Count occurrences of old_str
        count = content.count(args.old_str)
        if count == 0:
            raise ValueError(f"Text not found in {args.path}")
        elif count > 1:
            raise ValueError(f"Text appears {count} times in {args.path}. Must be unique.")
        
        # Replace and save
        new_content = content.replace(args.old_str, args.new_str)
        self._data[path_cleaned] = new_content
        
        return ToolResult(text=f"File {args.path} has been edited")
    
    
    def insert(self, args: BetaMemoryTool20250818InsertCommand) -> ToolResult:
        path_cleaned = self._validate_path(args.path)
        insert_line = args.insert_line
        insert_text = args.insert_text
        
        # Check if file exists
        if path_cleaned not in self._data:
            raise FileNotFoundError(f"File not found: {args.path}")
        
        content = self._data[path_cleaned]
        
        if content is None:
            raise ValueError(f"File not found: {args.path}")
        
        lines = content.splitlines()
        
        # Validate insert_line is in valid range
        if insert_line < 0 or insert_line > len(lines):
            raise ValueError(f"Invalid insert_line {insert_line}. Must be 0-{len(lines)}")
        
        # Insert text at specified line
        lines.insert(insert_line, insert_text.rstrip("\n"))
        
        # Update content in dictionary
        self._data[path_cleaned] = "\n".join(lines) + "\n"
        
        return ToolResult(text=f"Text inserted at line {insert_line} in {args.path}")
    
    
    def delete(self, args: BetaMemoryTool20250818DeleteCommand) -> ToolResult:
        path_cleaned = self._validate_path(args.path)
        
        # Prevent deleting the root memories directory
        if args.path == "/memories":
            raise ValueError("Cannot delete the /memories directory itself")
        
        # Check if it's a file
        if path_cleaned in self._data:
            del self._data[path_cleaned]
            return ToolResult(text=f"File deleted: {args.path}")
        
        # Check if it's a directory (has children with this prefix)
        prefix = path_cleaned + "/"
        keys_to_delete = [key for key in self._data.keys() if key.startswith(prefix)]
        
        if keys_to_delete:
            # Delete all files in the directory
            for key in keys_to_delete:
                del self._data[key]
            return ToolResult(text=f"Directory deleted: {args.path}")
        
        # Path not found
        raise FileNotFoundError(f"Path not found: {args.path}")
    
    
    def rename(self, args: BetaMemoryTool20250818RenameCommand) -> ToolResult:
        old_path_cleaned = self._validate_path(args.old_path)
        new_path_cleaned = self._validate_path(args.new_path)
        
        # Check if old path exists (as file or directory)
        old_is_file = old_path_cleaned in self._data
        old_is_dir = any(key.startswith(old_path_cleaned + "/") for key in self._data.keys())
        
        if not old_is_file and not old_is_dir:
            raise FileNotFoundError(f"Source path not found: {args.old_path}")
        
        # Check if new path already exists
        new_exists_as_file = new_path_cleaned in self._data
        new_exists_as_dir = any(key.startswith(new_path_cleaned + "/") for key in self._data.keys())
        
        if new_exists_as_file or new_exists_as_dir:
            raise ValueError(f"Destination already exists: {args.new_path}")
        
        # Perform rename
        if old_is_file:
            # Simple file rename
            self._data[new_path_cleaned] = self._data[old_path_cleaned]
            del self._data[old_path_cleaned]
        else:
            # Directory rename - update all keys with the old prefix
            old_prefix = old_path_cleaned + "/"
            new_prefix = new_path_cleaned + "/"
            keys_to_rename = [key for key in self._data.keys() if key.startswith(old_prefix)]
            
            for old_key in keys_to_rename:
                new_key = new_prefix + old_key[len(old_prefix):]
                self._data[new_key] = self._data[old_key]
                del self._data[old_key]
        
        return ToolResult(text=f"Renamed {args.old_path} to {args.new_path}")
    

    async def get_anthropic_definition(self) -> dict:
        return {
            "type": "memory_20250818",
            "name": "memory"
        }
    
    async def get_openai_definition(self) -> dict:
        raise NotImplementedError("OpenAI definition not available for this tool")

    def get_ui_tool_name(self, args) -> str:
        return "memory"