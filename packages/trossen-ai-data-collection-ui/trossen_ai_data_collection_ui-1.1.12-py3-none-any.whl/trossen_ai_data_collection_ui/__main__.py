import shutil
import sys

from PySide6.QtWidgets import QApplication

from trossen_ai_data_collection_ui.ui.main_window import MainWindow
from trossen_ai_data_collection_ui.utils.constants import (
    DEFAULT_CONFIGS_ROOT,
    PERSISTENT_CONFIGS_ROOT,
)


def main() -> None:
    """
    Entry point for the Trossen AI Data Collection application.

    This function initializes default configurations, the QApplication, sets the application style,
    creates the main window, and starts the application's event loop.
    """

    # Check if the default configuration file directory exist.
    # If not, copy it from the package's default configuration directory.
    if not PERSISTENT_CONFIGS_ROOT.exists():
        # Make the directory for persistent configs if it doesn't exist.
        PERSISTENT_CONFIGS_ROOT.mkdir(parents=True, exist_ok=True)
        # Copy the default robot configuration file to the persistent configs directory.
        shutil.copytree(DEFAULT_CONFIGS_ROOT, PERSISTENT_CONFIGS_ROOT, dirs_exist_ok=True)

    app = QApplication(sys.argv)  # Create the application instance.
    app.setStyle("Fusion")  # Set the application style to 'Fusion'.

    window = MainWindow()  # Create the main window instance.
    window.showFullScreen()  # Show the main window in full-screen mode.
    # window.show()  # Uncomment to show the window in a normal mode.

    sys.exit(app.exec())  # Execute the application's event loop and exit cleanly.


if __name__ == "__main__":
    main()  # Run the main function if the script is executed directly.
