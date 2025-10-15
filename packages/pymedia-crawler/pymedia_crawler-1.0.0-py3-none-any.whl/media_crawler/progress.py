"""
Progress display utilities for cleaner output.
Shows a single-page progress view instead of scrolling logs.
"""
import sys
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressStats:
    """Statistics for progress display."""
    current_depth: int = 0
    max_depth: int = 0
    urls_processed: int = 0
    urls_in_queue: int = 0
    links_found: int = 0
    downloads_completed: int = 0
    downloads_failed: int = 0
    current_url: str = ""
    status: str = "Initializing..."


class ProgressDisplay:
    """
    Single-page progress display with live updates.
    Replaces verbose logging with a clean progress view.
    """
    
    def __init__(self, quiet: bool = False):
        """
        Initialize progress display.
        
        Args:
            quiet: If True, suppress all output except errors
        """
        self.quiet = quiet
        self.stats = ProgressStats()
        self.start_time = time.time()
        self.last_update = 0
        self._is_terminal = sys.stdout.isatty()
        
    def update(self, **kwargs):
        """
        Update progress statistics and redraw display.
        
        Args:
            **kwargs: Any ProgressStats field to update
        """
        if self.quiet:
            return
            
        # Update stats
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
        
        # Throttle updates to avoid flickering (max 10 updates/sec)
        current_time = time.time()
        if current_time - self.last_update < 0.1:
            return
        self.last_update = current_time
        
        self._draw()
    
    def _draw(self):
        """Draw the progress display."""
        if not self._is_terminal:
            # If not a terminal, just print simple status
            print(f"[{self.stats.status}] Depth {self.stats.current_depth}/{self.stats.max_depth} | "
                  f"Processed: {self.stats.urls_processed} | "
                  f"Downloaded: {self.stats.downloads_completed}", flush=True)
            return
        
        # Clear screen and move cursor to top
        sys.stdout.write('\033[2J\033[H')
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Build display
        lines = [
            "=" * 70,
            "🔍 MEDIA CRAWLER - PROGRESS",
            "=" * 70,
            "",
            f"Status: {self.stats.status}",
            f"Elapsed Time: {hours:02d}:{minutes:02d}:{seconds:02d}",
            "",
            "─" * 70,
            "CRAWL PROGRESS",
            "─" * 70,
            f"  Depth: {self.stats.current_depth} / {self.stats.max_depth}",
            f"  URLs Processed: {self.stats.urls_processed}",
            f"  URLs in Queue: {self.stats.urls_in_queue}",
            f"  Links Found: {self.stats.links_found}",
            "",
            "─" * 70,
            "DOWNLOAD PROGRESS",
            "─" * 70,
            f"  ✓ Completed: {self.stats.downloads_completed}",
            f"  ✗ Failed: {self.stats.downloads_failed}",
            f"  Success Rate: {self._success_rate()}%",
            "",
        ]
        
        # Add current URL (truncated if too long)
        if self.stats.current_url:
            current_url = self.stats.current_url
            if len(current_url) > 65:
                current_url = current_url[:62] + "..."
            lines.extend([
                "─" * 70,
                "CURRENT URL",
                "─" * 70,
                f"  {current_url}",
                "",
            ])
        
        lines.append("=" * 70)
        lines.append("Press Ctrl+C to stop")
        lines.append("")
        
        # Print all lines
        sys.stdout.write('\n'.join(lines))
        sys.stdout.flush()
    
    def _success_rate(self) -> str:
        """Calculate download success rate."""
        total = self.stats.downloads_completed + self.stats.downloads_failed
        if total == 0:
            return "N/A"
        rate = (self.stats.downloads_completed / total) * 100
        return f"{rate:.1f}"
    
    def finish(self, message: str = "Crawl completed!"):
        """
        Show final summary.
        
        Args:
            message: Completion message
        """
        if self.quiet:
            return
        
        # Update status and draw one final time
        self.stats.status = message
        self._draw()
        
        # Print summary
        elapsed = time.time() - self.start_time
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"  Total URLs Processed: {self.stats.urls_processed}")
        print(f"  Total Links Found: {self.stats.links_found}")
        print(f"  Downloads Completed: {self.stats.downloads_completed}")
        print(f"  Downloads Failed: {self.stats.downloads_failed}")
        print(f"  Total Time: {elapsed:.1f}s")
        print("=" * 70)
        print()
    
    def error(self, message: str):
        """
        Display an error message.
        
        Args:
            message: Error message to display
        """
        # Always show errors even in quiet mode
        if self._is_terminal:
            sys.stdout.write('\033[2J\033[H')  # Clear screen
        
        print("=" * 70, file=sys.stderr)
        print("❌ ERROR", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"  {message}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        sys.stderr.flush()


class SimpleProgress:
    """
    Simple progress indicator for non-interactive use.
    Prints updates as single lines without clearing screen.
    """
    
    def __init__(self):
        self.last_message = ""
    
    def update(self, message: str):
        """Print a progress update."""
        if message != self.last_message:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
            self.last_message = message
    
    def finish(self, message: str = "Done!"):
        """Print completion message."""
        print(f"[{time.strftime('%H:%M:%S')}] ✓ {message}")
    
    def error(self, message: str):
        """Print error message."""
        print(f"[{time.strftime('%H:%M:%S')}] ✗ {message}", file=sys.stderr)
