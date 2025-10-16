from abc import ABC, abstractmethod
from typing import Any, List, Optional

class SFNBaseView(ABC):
    def __init__(self, title: str = "Feature Suggestion App"):
        self.title = title

    @abstractmethod
    def display_title(self):
        """Display the app title."""
        pass

    @abstractmethod
    def show_message(self, message: str, message_type: str = "info"):
        """Show a message of a specific type (info, success, error)."""
        pass

    @abstractmethod
    def display_header(self, text: str):
        """Display a section header."""
        pass

    @abstractmethod
    def display_subheader(self, text: str):
        """Display a subsection header."""
        pass

    @abstractmethod
    def display_markdown(self, text: str):
        """Display markdown formatted text."""
        pass

    @abstractmethod
    def create_columns(self, num_columns: int):
        """Create multiple columns for layout."""
        pass

    @abstractmethod
    def file_uploader(self, label: str, accepted_types: List[str]) -> Any:
        """Display a file upload widget."""
        pass

    @abstractmethod
    def display_dataframe(self, data: Any):
        """Display a dataframe."""
        pass

    @abstractmethod
    def display_spinner(self, text: str) -> Any:
        """Display a loading spinner with text."""
        pass

    @abstractmethod
    def radio_select(self, label: str, options: List[str], key: Optional[str] = None) -> str:
        """Display a radio button group."""
        pass

    @abstractmethod
    def display_button(self, label: str, key: Optional[str] = None) -> bool:
        """Display a button and return its clicked state."""
        pass

    @abstractmethod
    def load_progress_bar(self, progress: float):
        """Display a progress bar with given progress (0-1)."""
        pass

    @abstractmethod
    def create_download_button(self, label: str, data: Any, file_name: str, mime_type: str):
        """Create a download button for files."""
        pass

    @abstractmethod
    def create_container(self) -> Any:
        """Create a container for grouping elements."""
        pass

    @abstractmethod
    def stop_execution(self):
        """Stop the current execution flow."""
        pass

    @abstractmethod
    def rerun_script(self):
        """Rerun the current script."""
        pass

    @abstractmethod
    def make_empty(self):
        """Create an empty element that can be updated later."""
        pass

    @abstractmethod
    def update_progress(self, progress_bar: Any, value: float):
        """Update a progress bar with a new value."""
        pass

    @abstractmethod
    def update_text(self, text_element: Any, new_text: str):
        """Update a text element with new content."""
        pass

    @abstractmethod
    def create_progress_container(self):
        """Create a progress bar and status text container."""
        pass

    @abstractmethod    
    def select_box(self, label: str, options: List[str], key: Optional[str] = None) -> str:
        pass