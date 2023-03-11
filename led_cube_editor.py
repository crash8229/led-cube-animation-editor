from led_cube_editor.editor import LEDCubeEditor
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication()
    window = LEDCubeEditor()
    window.show()
    app.exec()
