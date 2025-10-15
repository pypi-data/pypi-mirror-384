from PyQt5.QtWidgets import QPushButton

def new_button(layout, label, on_click, enable: bool):
    button = QPushButton(label)
    button.setEnabled(enable)
    button.clicked.connect(on_click)
    layout.addWidget(button)
    return button
