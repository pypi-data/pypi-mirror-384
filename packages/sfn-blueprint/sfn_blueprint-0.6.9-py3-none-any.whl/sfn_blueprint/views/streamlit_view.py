import os
from pathlib import Path
import streamlit as st
from .base_view import SFNBaseView
from typing import Any, List, Optional

class SFNStreamlitView(SFNBaseView):
    def display_title(self):
        st.title(self.title)

    def show_message(self, message: str, message_type: str = "info"):
        print('message',message,'message_type',message_type)
        if message_type == "info":
            st.info(message)
        elif message_type == "success":
            st.success(message)
        elif message_type == "error":
            st.error(message)
        elif message_type == "warning":
            st.warning(message)

    def display_header(self, text: str):
        st.header(text)

    def display_subheader(self, text: str):
        st.subheader(text)

    def display_markdown(self, text: str):
        st.markdown(text)

    def create_columns(self, num_columns: int):
        return st.columns(num_columns)

    def file_uploader(self, label: str, accepted_types: List[str]) -> Any:
        return st.file_uploader(label, type=accepted_types)
    
    def file_uploader_with_key(self, label: str, key: str, accepted_types: List[str]) -> Optional[str]:
        return st.file_uploader(label, key=key, type=accepted_types)
    
    def save_uploaded_file(self, uploaded_file: Any) -> Optional[str]:
        """Temporarily save uploaded file to create path and access via DASK"""
        if uploaded_file is not None:
            # Define the temp directory to save files
            temp_dir = Path('./temp_files')
            temp_dir.mkdir(exist_ok=True)  # Create directory if not exists

            # Create a valid file path
            file_path = temp_dir / uploaded_file.name

            # Save the file to the specified path
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Return the file path for further processing
            return str(file_path)
        return None
    
    def delete_uploaded_file(self, file_path: str) -> bool:
        """Delete the saved temp file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            else:
                self.show_message(f"File {file_path} does not exist.", "error")
        except Exception as e:
            self.show_message(f"Error deleting file: {e}", "error")
        
        return False

    def display_dataframe(self, data: Any):
        st.dataframe(data)

    def display_spinner(self, text: str):
        return st.spinner(text)

    def radio_select(self, label: str, options: List[str], key: Optional[str] = None) -> str:
        return st.radio(label, options, key=key)

    def load_progress_bar(self, progress: float):
        st.progress(progress)

    def create_download_button(self, label: str, data: Any, file_name: str, mime_type: str):
        st.download_button(
            label=label,
            data=data,
            file_name=file_name,
            mime=mime_type
        )

    def create_container(self):
        return st.container()

    def stop_execution(self):
        st.stop()

    def rerun_script(self):
        st.rerun()

    def make_empty(self):
        return st.empty()


    def update_text(self, text_element: st.delta_generator.DeltaGenerator, new_text: str):
        text_element.text(new_text)

    
    def load_progress_bar(self, progress: float):
        """Display a progress bar with given progress (0-1)."""
        return st.progress(progress)

    def update_progress(self, progress_bar: Any, value: float):
        """Update a progress bar with a new value."""
        # In Streamlit, we can just set the value directly on the progress bar
        progress_bar.progress(min(1.0, max(0.0, value)))

    def create_progress_container(self):
        """Create a progress bar and status text container."""
        container = st.container()
        with container:
            progress_bar = self.load_progress_bar(0.0)
            status_text = self.make_empty()
        return progress_bar, status_text

    @property
    def session_state(self):
        """Access to Streamlit's session state"""
        return st.session_state
    
    def select_box(self, label: str, options: List[str], key: Optional[str] = None, default: Optional[str] = None) -> str:
        # Find the index of the default value if provided
        if default and default in options:
            index = options.index(default)
        else:
            index = 0
        return st.selectbox(label, options, key=key, index=index)
    
    def checkbox(self, label=None, key=None, value=False, disabled=False, label_visibility="visible"):
        """Create a checkbox with a default hidden label if none provided"""
        if label is None or label == "":
            # Generate a label based on the key if no label is provided
            label = key if key else "checkbox"
        return st.checkbox(
            label=label,
            key=key,
            value=value,
            disabled=disabled,
            label_visibility=label_visibility
        )

    def display_button(self, label: str, key: Optional[str] = None, use_container_width: bool = False) -> bool:
        """Display a button with proper labeling"""
        button_key = key if key else f"button_{label}"
        return st.button(label=label, key=button_key, use_container_width=use_container_width)