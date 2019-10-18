from qqt import QtWidgets
from brick import lib


class BlockMenuWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BlockMenuWidget, self).__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        label = QtWidgets.QLabel("+")
        layout.addWidget(label)

        menuBar = QtWidgets.QMenuBar()

        blockMap = lib.collectBlocksByCategory()

        for category, opclasses in blockMap.items():
            categoryMenu = QtWidgets.QMenu(category, menuBar)
            categoryMenu.setStyleSheet("QMenu {border: 1px solid black;}")
            menuBar.addMenu(categoryMenu)

            for opcls in opclasses:
                action = QtWidgets.QAction(opcls.__name__, self)
                categoryMenu.addAction(action)

        layout.addWidget(menuBar)

    @property
    def blueprintWidget(self):
        return self.parentWidget()
