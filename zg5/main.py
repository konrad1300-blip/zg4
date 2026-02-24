import sys
from PySide6.QtWidgets import QApplication
from models import ZarzadcaDanych
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Zgrzewanie 4.0")

    zarzadca = ZarzadcaDanych()
    window = MainWindow(zarzadca)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()