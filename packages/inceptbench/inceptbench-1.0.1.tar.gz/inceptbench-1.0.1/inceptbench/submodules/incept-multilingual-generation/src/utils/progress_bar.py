"""
Progress bar utility for replacing verbose logging with visual indicators.
Maintains error logging while reducing noise from repetitive progress updates.
"""
import sys
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ProgressBar:
    """
    A simple progress bar that replaces verbose logging for long-running operations.
    Automatically handles updates and completion logging.
    """

    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
        self.last_log_time = 0
        self.completed = False

    def update(self, increment: int = 1, details: str = "") -> None:
        """Update progress bar and optionally log details if important."""
        self.current += increment

        # Avoid excessive console updates - only update every 0.1 seconds
        current_time = time.time()
        if current_time - self.last_log_time < 0.1 and self.current < self.total:
            return

        self.last_log_time = current_time
        self._draw_progress_bar(details)

        if self.current >= self.total and not self.completed:
            self.complete()

    def _draw_progress_bar(self, details: str = "") -> None:
        """Draw the progress bar to console."""
        if self.total == 0:
            return

        percentage = min(100, (self.current / self.total) * 100)
        filled_width = int(self.width * self.current / self.total)

        bar = '█' * filled_width + '░' * (self.width - filled_width)

        # Format: [Description] [████████████████████] 15/20 (75.2%) - details
        status = f"\r{self.description} [{bar}] {self.current}/{self.total} ({percentage:.1f}%)"
        if details:
            status += f" - {details}"

        print(status, end='', flush=True)

    def complete(self, final_message: str = "") -> None:
        """Mark progress as complete and log final status."""
        if self.completed:
            return

        self.completed = True
        elapsed = time.time() - self.start_time

        # Clear the progress line and log completion
        print()  # New line after progress bar

        if final_message:
            logger.info(f"✅ {self.description}: {final_message} ({elapsed:.2f}s)")
        else:
            logger.info(f"✅ {self.description}: Complete - {self.current}/{self.total} ({elapsed:.2f}s)")

    def error(self, error_message: str) -> None:
        """Log an error while maintaining progress context."""
        print()  # New line after progress bar
        logger.error(f"❌ {self.description}: {error_message}")

    def warning(self, warning_message: str) -> None:
        """Log a warning while maintaining progress context."""
        print()  # New line after progress bar
        logger.warning(f"⚠️  {self.description}: {warning_message}")


class ModuleProgressTracker:
    """
    Tracks progress across multiple modules with hierarchical progress bars.
    Useful for orchestrator-level progress tracking.
    """

    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.overall_start_time = time.time()

    def start_module(self, module_name: str, description: str, total_items: int = 0) -> ProgressBar:
        """Start tracking a module's progress."""
        progress_bar = ProgressBar(total_items, f"📦 {module_name}: {description}")

        self.modules[module_name] = {
            'progress_bar': progress_bar,
            'start_time': time.time(),
            'description': description
        }

        logger.info(f"🚀 {module_name} START: {description}")
        return progress_bar

    def complete_module(self, module_name: str, summary: str = "") -> None:
        """Complete a module and log final statistics."""
        if module_name not in self.modules:
            return

        module_data = self.modules[module_name]
        progress_bar = module_data['progress_bar']
        elapsed = time.time() - module_data['start_time']

        progress_bar.complete(summary or f"{module_data['description']} complete")

    def log_error(self, module_name: str, error_message: str) -> None:
        """Log an error for a specific module."""
        if module_name in self.modules:
            self.modules[module_name]['progress_bar'].error(error_message)
        else:
            logger.error(f"❌ {module_name}: {error_message}")

    def log_warning(self, module_name: str, warning_message: str) -> None:
        """Log a warning for a specific module."""
        if module_name in self.modules:
            self.modules[module_name]['progress_bar'].warning(warning_message)
        else:
            logger.warning(f"⚠️  {module_name}: {warning_message}")


# Global instance for easy access across modules
module_tracker = ModuleProgressTracker()