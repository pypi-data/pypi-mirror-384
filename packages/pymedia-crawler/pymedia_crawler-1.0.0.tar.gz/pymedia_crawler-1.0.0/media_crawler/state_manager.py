"""
State management for crawler (in-memory only).
"""
import logging
from typing import List, Tuple, Set, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CrawlerState:
    """Data class for crawler state."""
    queue: List[Tuple[str, int]] = field(default_factory=list)
    visited: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization."""
        return {
            'queue': self.queue,
            'visited': list(self.visited)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CrawlerState':
        """Create state from dictionary."""
        return cls(
            queue=data.get('queue', []),
            visited=set(data.get('visited', []))
        )


class StateManager:
    """Manager for crawler state (in-memory only, no file persistence)."""
    
    def __init__(self, state_path: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            state_path: Ignored - kept for compatibility
        """
        self.state_path = state_path  # Keep for compatibility but not used
        logger.info("State manager initialized (in-memory only, no file persistence)")
    
    def save_state(self, state: CrawlerState) -> None:
        """
        Save crawler state (no-op, state only kept in memory).
        
        Args:
            state: Crawler state (not persisted to disk)
        """
        # No-op: We don't save to file anymore
        logger.debug(
            f"State snapshot: {len(state.queue)} URLs in queue, "
            f"{len(state.visited)} visited"
        )
    
    def load_state(self) -> CrawlerState:
        """
        Load crawler state (always returns fresh state).
        
        Returns:
            New empty state (no file loading)
        """
        logger.info("Starting with fresh state (no file persistence)")
        return CrawlerState()
    
    def clear_state(self) -> None:
        """Clear state (no-op since we don't use files)."""
        logger.debug("State clear requested (no files to remove)")
