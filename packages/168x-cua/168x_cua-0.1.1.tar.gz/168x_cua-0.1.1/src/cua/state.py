# state.py
from __future__ import annotations
import os
import tempfile
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Optional, Callable
from contextlib import asynccontextmanager
from pydantic import BaseModel, ValidationError
from enum import Enum

from cua.settings import settings


class FSMState(str, Enum):
    """FSM State enum - inherits from str for better JSON serialization"""
    INITIALIZED = "initialized"
    REGISTERED = "registered"


class Model(str, Enum):
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    

class StateModel(BaseModel):
    """Pure Pydantic model for state data with validation"""
    fsm_state: FSMState = FSMState.INITIALIZED
    latest_message_updated_at: Optional[datetime] = None
    
    model: Model = Model.CLAUDE_SONNET_4_5
    system_prompt: str = ""
    instructions: str = ""
    
    # Callback to notify parent State when fields change
    _on_change_callback: Optional[Callable[[], None]] = None
    
    model_config = {
        "use_enum_values": True,  # Keep enum objects for type safety
        "validate_assignment": True,  # Validate on attribute assignment
        "arbitrary_types_allowed": True,  # Allow callable type
    }
    
    def __setattr__(self, name: str, value):
        """Override to notify parent State of changes"""
        super().__setattr__(name, value)
        # Notify parent State that data changed (skip internal fields)
        if not name.startswith('_') and self._on_change_callback:
            self._on_change_callback()


class State:
    """State manager with atomic JSON persistence.
    
    Access state data through the `data` property:
        state.data.fsm_state = FSMState.INITIALIZED
        state.data.latest_message_updated_at = datetime.now()
    """
    
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._lock = RLock()
        self._data = StateModel()
        self._loaded = False
        self._dirty = False
        # Set callback to mark State as dirty when data changes
        self._data._on_change_callback = self._mark_dirty
        self._ensure_loaded()
    
    @property
    def data(self) -> StateModel:
        """Access to the state data model with full editor support"""
        return self._data
    
    def _mark_dirty(self):
        """Mark state as dirty (called by StateModel when fields change)"""
        self._dirty = True
    
    def _ensure_loaded(self):
        """Load state from disk if not already loaded"""
        if self._loaded:
            return
        if self._path.exists():
            try:
                # Use Pydantic v2 method for JSON deserialization
                json_content = self._path.read_text(encoding="utf-8")
                self._data = StateModel.model_validate_json(json_content)
                # Set callback after loading
                self._data._on_change_callback = self._mark_dirty
            except Exception:
                # Backup corrupt file
                self._path.rename(self._path.with_suffix(".corrupt"))
                self._data = StateModel()
                self._data._on_change_callback = self._mark_dirty
        self._loaded = True
    
    def __setattr__(self, name: str, value):
        """Allow direct attribute access for convenience.
        
        Supports both patterns:
        - state.fsm_state = value  (no autocomplete)
        - state.data.fsm_state = value  (full editor support)
        """
        if name.startswith('_'):
            # Internal attributes - set directly
            super().__setattr__(name, value)
        else:
            # Forward to state data model
            setattr(self._data, name, value)
    
    def __getattr__(self, name: str):
        """Allow direct attribute access for convenience.
        
        Supports both patterns:
        - state.fsm_state  (no autocomplete)
        - state.data.fsm_state  (full editor support)
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._data, name)
    
    def commit(self):
        """Atomically write validated JSON to disk using Pydantic serialization."""
        with self._lock:
            if not self._dirty:
                return
            try:
                # Validate the current state
                validated = StateModel.model_validate(self._data.model_dump())
            except ValidationError as e:
                raise ValueError(f"State validation failed: {e}") from e
            
            # Use Pydantic's native JSON serialization
            json_content = validated.model_dump_json(indent=2)
            
            # Ensure parent directory exists
            self._path.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic write
            tmp = tempfile.NamedTemporaryFile(
                "w", 
                delete=False, 
                dir=self._path.parent, 
                encoding="utf-8"
            )
            tmp.write(json_content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, self._path)
            self._dirty = False
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for atomic state transactions.
        
        Usage:
            async with state.transaction():
                state.data.fsm_state = FSMState.INITIALIZED
                state.data.latest_message_updated_at = datetime.now()
            # Automatically commits on successful exit
        
        If an exception occurs within the context, changes are not committed.
        """
        # Save current state for potential rollback
        snapshot = self._data.model_dump()
        
        try:
            yield self
            # Commit on successful completion
            self.commit()
        except Exception:
            # Rollback on exception - restore from snapshot
            self._data = StateModel.model_validate(snapshot)
            self._data._on_change_callback = self._mark_dirty
            self._dirty = False
            raise
    
    def as_dict(self):
        """Return state as dictionary using Pydantic serialization"""
        return self._data.model_dump()
    
    def as_json(self) -> str:
        """Return state as JSON string using Pydantic serialization"""
        return self._data.model_dump_json(indent=2)


# Singleton instance (can be replaced with dependency injection if needed)
state = State(Path(settings.CUA_ROOT_DIR) / "data" / "state.json")