from typing import Optional, Tuple

from qtpy.QtCore import Signal, Qt, QRect, QSize, QPoint, QObject, QEvent
from qtpy.QtWidgets import *
from qtpy import QtGui

from led_cube_editor import __version__
from led_cube_view import LEDCubeView  # type:ignore
from qtpy_led import Led  # type:ignore


class WidgetWithLabel(QWidget):
    def __init__(
        self,
        widget: QWidget,
        label_text: str,
        label_position: str = "left",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.widget: QWidget = widget
        self.widget.setParent(self)
        self.label = QLabel(label_text, self)  # type: ignore
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)  # type: ignore
        self.label.setContentsMargins(3, 0, 3, 0)
        label_position = label_position.lower()
        if label_position == "left":
            self.setLayout(QHBoxLayout())
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.layout().addWidget(self.label)
            self.layout().addWidget(self.widget)
        elif label_position == "right":
            self.setLayout(QHBoxLayout())
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.layout().addWidget(self.widget)
            self.layout().addWidget(self.label)
        elif label_position == "top":
            self.setLayout(QVBoxLayout())
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
            )
            self.layout().addWidget(self.label)
            self.layout().addWidget(self.widget)
        elif label_position == "bottom":
            self.setLayout(QVBoxLayout())
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
            )
            self.layout().addWidget(self.widget)
            self.layout().addWidget(self.label)
        else:
            raise ValueError(
                f"Invalid position for label_position: {label_position}\nValid options: left, right, top, bottom"
            )


class LEDWithPosition(Led):
    led_changed: Signal = Signal(int, int, int, bool)  # type: ignore

    def __init__(
        self, x: int, y: int, z: int, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent=parent, on_color=Led.red)
        self.setEnabled(True)
        self.setFixedSize(30, 30)
        self.__x = x
        self.__y = y
        self.__z = z
        self.status_changed.connect(self.__emit_led_changed)  # type: ignore
        self.__last_state: bool = False

    def __emit_led_changed(self, state: bool) -> None:
        if state != self.__last_state:
            self.led_changed.emit(self.__x, self.__y, self.__z, state)
            self.__last_state = state

    @property
    def x(self) -> int:
        return self.__x

    @property
    def y(self) -> int:
        return self.__y

    @property
    def z(self) -> int:
        return self.__z

    @property
    def state(self) -> bool:
        return self.is_on()


class EditorControls(QGroupBox):
    layer_changed: Signal = Signal(int)  # type: ignore
    frame_changed: Signal = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Editor Options", parent)  # type: ignore
        self._layout: QVBoxLayout = QVBoxLayout(self)  # type: ignore

        #### Selectors ####
        selectors = QHBoxLayout()
        self._layout.addLayout(selectors)

        # Frame Selector
        frame_selector = QWidget(self)
        frame_selector_lo = QVBoxLayout(frame_selector)  # type: ignore

        self._frame_menu_up_button: QPushButton = QPushButton("˄", frame_selector)
        self._frame_menu: QComboBox = QComboBox(frame_selector)
        self._frame_menu_down_button: QPushButton = QPushButton("˅", frame_selector)

        frame_selector_lo.addWidget(self._frame_menu_up_button)
        frame_selector_lo.addWidget(self._frame_menu)
        frame_selector_lo.addWidget(self._frame_menu_down_button)

        self._frame_menu_up_button.clicked.connect(lambda x: self.__button_change_menu(self._frame_menu, True))  # type: ignore
        self._frame_menu_down_button.clicked.connect(lambda x: self.__button_change_menu(self._frame_menu, False))  # type: ignore
        self._frame_menu.currentIndexChanged.connect(lambda x: self.__update_button_states(self._frame_menu, self._frame_menu_up_button, self._frame_menu_down_button))  # type: ignore
        self._frame_menu.currentIndexChanged.connect(self.frame_changed)  # type: ignore

        self.__update_button_states(
            self._frame_menu, self._frame_menu_up_button, self._frame_menu_down_button
        )

        frame_selector_with_label = WidgetWithLabel(
            frame_selector, "Frame:", "left", self
        )
        selectors.addWidget(frame_selector_with_label)

        # Layer Selector
        layer_selector = QWidget(self)

        layer_selector_lo = QVBoxLayout(layer_selector)  # type: ignore
        self._layer_menu_up_button: QPushButton = QPushButton("˄", layer_selector)
        self._layer_menu: QComboBox = QComboBox(layer_selector)
        self._layer_menu_down_button: QPushButton = QPushButton("˅", layer_selector)

        layer_selector_lo.addWidget(self._layer_menu_up_button)
        layer_selector_lo.addWidget(self._layer_menu)
        layer_selector_lo.addWidget(self._layer_menu_down_button)

        self._layer_menu_up_button.clicked.connect(lambda x: self.__button_change_menu(self._layer_menu, True))  # type: ignore
        self._layer_menu_down_button.clicked.connect(lambda x: self.__button_change_menu(self._layer_menu, False))  # type: ignore
        self._layer_menu.currentIndexChanged.connect(lambda x: self.__update_button_states(self._layer_menu, self._layer_menu_up_button, self._layer_menu_down_button))  # type: ignore
        self._layer_menu.currentIndexChanged.connect(self.layer_changed)  # type: ignore

        self.__update_button_states(
            self._layer_menu, self._layer_menu_up_button, self._layer_menu_down_button
        )

        layer_selector_with_label = WidgetWithLabel(
            layer_selector, "Layer:", "left", self
        )
        layer_selector_with_label.label.setStyleSheet(
            "QLabel { background-color: green; color: white }"
        )
        selectors.addWidget(layer_selector_with_label)

    @staticmethod
    def __button_change_menu(menu: QComboBox, direction: bool) -> None:
        idx = menu.currentIndex()
        if direction and idx + 1 < menu.count():
            menu.setCurrentIndex(idx + 1)
        elif not direction and idx - 1 >= 0:
            menu.setCurrentIndex(idx - 1)

    @staticmethod
    def __update_button_states(
        menu: QComboBox, up_button: QPushButton, down_button: QPushButton
    ) -> None:
        idx = menu.currentIndex()
        if idx == menu.count() - 1:
            up_button.setEnabled(False)
        else:
            up_button.setEnabled(True)
        if idx <= 0:
            down_button.setEnabled(False)
        else:
            down_button.setEnabled(True)

    def set_layers(self, number: int) -> None:
        self._layer_menu.clear()
        for i in range(number):
            self._layer_menu.addItem(f"{i + 1:02d}")
        self.__update_button_states(
            self._layer_menu, self._layer_menu_up_button, self._layer_menu_down_button
        )

    def set_frames(self, number: int) -> None:
        self._frame_menu.clear()
        for i in range(number):
            self._frame_menu.addItem(f"{i + 1:02d}")
        self.__update_button_states(
            self._frame_menu, self._frame_menu_up_button, self._frame_menu_down_button
        )


class Layer(QWidget):
    led_changed: Signal = Signal(int, int, int, bool)  # type: ignore

    def __init__(self, parent: Optional[QWidget], x: int, y: int, z: int) -> None:
        super().__init__(parent)
        self._layout: QGridLayout = QGridLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(40)
        self.layer_num = z
        for r in range(y):
            label = QLabel(f"{x - r}", self)  # type: ignore
            label.setStyleSheet("QLabel { background-color: yellow; color: black}")
            label.setContentsMargins(0, 0, 0, 0)
            self._layout.addWidget(label, r, 0, 1, 1, Qt.AlignmentFlag.AlignRight)
            self._layout.setRowStretch(r, 1)
            for c in range(x):
                led = LEDWithPosition(c, y - r - 1, self.layer_num, self)
                led.led_changed.connect(self.led_changed)
                self._layout.addWidget(
                    led, r, c + 1, 1, 1, Qt.AlignmentFlag.AlignCenter
                )
                self._layout.setColumnStretch(c + 1, 1)
        for c in range(y):
            label = QLabel(f"{c + 1}", self)  # type: ignore
            label.setStyleSheet("QLabel { background-color: blue; color: white}")
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            label.setContentsMargins(0, 0, 0, 0)
            self._layout.addWidget(label, x, c + 1, 1, 1, Qt.AlignmentFlag.AlignTop)

    def get_leds(self) -> Tuple[LEDWithPosition, ...]:
        return tuple(
            self._layout.itemAt(i).wid  # type: ignore
            for i in range(self._layout.count())
            if isinstance(self._layout.itemAt(i).wid, LEDWithPosition)  # type: ignore
        )


class Frame(QStackedWidget):
    led_changed: Signal = Signal(int, int, int, bool)  # type: ignore
    change_layer: Signal = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget], x: int, y: int, z: int, duration: int = 5) -> None:
        super().__init__(parent)
        self.__setup_layers(x, y, z)
        self.change_layer.connect(self.setCurrentIndex)
        self.__duration = duration
        self.__version = 1
        self.__type = 1

    def __setup_layers(self, x: int, y: int, z: int) -> None:
        for z_num in range(z):
            layer = Layer(self, x, y, z_num)
            layer.led_changed.connect(self.led_changed)
            self.addWidget(layer)

    def get_layers(self) -> Tuple[Layer, ...]:
        return tuple(self.widget(i) for i in range(self.count()))  # type: ignore

    @property
    def duration(self) -> int:
        return self.__duration

    @duration.setter
    def duration(self, ms: int) -> None:
        if not isinstance(ms, int):
            raise ValueError(f"Expected integer, got {type(ms)}")
        if 65535 >= ms >= 0:
            self.__duration = ms
        else:
            raise ValueError(f"Value out of range (65535 >= ms >= 0), got {ms} ")


class LEDLayerEditor(QGroupBox):
    led_changed: Signal = Signal(int, int, int, bool)  # type: ignore
    change_layer: Signal = Signal(int)  # type: ignore
    change_frame: Signal = Signal(int)  # type: ignore
    frame_changed: Signal = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Layer Editor", parent)  # type: ignore
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)  # type: ignore

        self.__rubberband: QRubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.__rubberband_origin: QPoint = QPoint()

        self._layout: QStackedLayout = QStackedLayout(self)  # type: ignore

        self.change_frame.connect(self._layout.setCurrentIndex)
        self._layout.currentChanged.connect(self.__change_frame)  # type: ignore
        self.__current_frame: Optional[int] = None

    @property
    def current_frame(self) -> Optional[int]:
        return self.__current_frame

    def get_frame(self, number: int) -> Frame:
        return self._layout.widget(number)  # type: ignore

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.__rubberband_origin = event.pos()
        self.__rubberband.setGeometry(QRect(self.__rubberband_origin, QSize()))  # type: ignore
        self.__rubberband.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        self.__rubberband.setGeometry(QRect(self.__rubberband_origin, event.pos()).normalized())  # type: ignore

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.__rubberband.hide()

    def set_cube_size(self, x: int, y: int, z: int, frames: int = 1):
        self._layout.blockSignals(True)
        while self._layout.count() > 0:
            frame: LEDLayerEditor.Frame = self._layout.itemAt(self._layout.count() - 1).wid  # type: ignore
            self._layout.removeWidget(frame)
            frame.deleteLater()

        for frame_num in range(frames):
            frame = Frame(self, x, y, z)

            self._layout.addWidget(frame)

        self._layout.blockSignals(False)
        self.__change_frame(self._layout.currentIndex())

    def __change_frame(self, idx: int) -> None:
        if self.__current_frame is not None:
            frame: Frame = self._layout.widget(self.__current_frame)  # type: ignore
            frame.led_changed.disconnect(self.led_changed)
            self.change_layer.disconnect(frame.change_layer)
        frame: Frame = self._layout.widget(idx)  # type: ignore
        frame.led_changed.connect(self.led_changed)
        self.change_layer.connect(frame.change_layer)
        self.frame_changed.emit(idx)


class LEDCubeEditor(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"LED Cube Editor {__version__}")
        main_widget = QWidget(self)
        main_layout: QGridLayout = QGridLayout(main_widget)
        main_widget.setLayout(main_layout)
        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)  # type: ignore
        self.setCentralWidget(main_widget)

        # Stylesheet for QGroupbox
        self.setStyleSheet(
            "QGroupBox { border: 1px solid black; border-radius: 5px; margin-top: 3ex; }"
            "\nQGroupBox::title { subcontrol-position: top center; subcontrol-origin: margin; }"
        )

        # Grid Stretch
        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(0, 10)
        main_layout.setColumnStretch(1, 12)

        # LED Editor Controls
        self.__editor_controls = EditorControls(self)
        main_layout.addWidget(self.__editor_controls, 0, 0)

        # LED Layer Edit
        self.__led_editor = LEDLayerEditor(parent=main_widget)
        main_layout.addWidget(self.__led_editor, 1, 0, 3, 1)
        self.__editor_controls.layer_changed.connect(self.__led_editor.change_layer)
        self.__editor_controls.frame_changed.connect(self.__led_editor.change_frame)

        # Cube View Controls
        cube_controls = QGroupBox("View Box Options", main_widget)  # type: ignore
        cube_controls_lo = QVBoxLayout()
        cube_controls.setLayout(cube_controls_lo)
        main_layout.addWidget(cube_controls, 0, 1)

        # Cube View
        self.__cube_view = LEDCubeView(main_widget)
        main_layout.addWidget(self.__cube_view, 1, 1, 3, 1)
        self.__config_list = self.__cube_view.config_list()
        self.__led_editor.led_changed.connect(self.__cube_view.set_led)
        self.__cube_view.setMinimumSize(550, 450)
        self.__led_editor.frame_changed.connect(self.__set_frame_view)
        # self.__led_editor.led_changed.connect(lambda xx, yy, zz, ss: print(f"X:{xx}, Y:{yy}, z:{zz}, State:{ss}, "))

        self.__load_cube("5x5x5", 3)

        # Attribute List
        # self.__attribute_list = QTableWidget(parent=main_widget)
        # self.__attribute_list.setColumnCount(2)
        # main_layout.addWidget(self.__attribute_list, 1, 1)

    # def eventFilter(self, watched: QObject, event: QEvent):
    #     if watched is self.__led_editor and event.type() == QEvent.Type.Resize:
    #         if self.__resize_do:
    #             self.__cube_view.setFixedWidth(event.size().width())
    #             self.__resize_skip = True
    #             self.__resize_do = False
    #         elif self.__resize_skip:
    #             self.__resize_skip = False
    #             return True
    #     elif watched is self and event.type() == QEvent.Type.NonClientAreaMouseButtonRelease:
    #         print("Released")
    #         self.__resize_do = True
    #     return False

    def __load_cube(self, config: str, frames: int = 1, custom: bool = False) -> None:
        if custom:
            raise NotImplementedError()
        elif config not in self.__config_list:
            raise ValueError(
                f"Invalid config: {config}\nValid options: {', '.join(self.__config_list)}"
            )
        self.__cube_view.load_cube(config)
        config_split = config.split("x")
        self.__led_editor.set_cube_size(*map(int, config_split), frames)  # type: ignore

        self.__editor_controls.set_layers(int(config_split[2]))
        self.__editor_controls.set_frames(frames)

    def __set_frame_view(self, idx: int) -> None:
        leds: Tuple[LEDWithPosition, ...] = tuple(
            led
            for layer in self.__led_editor.get_frame(idx).get_layers()
            for led in layer.get_leds()
        )
        for led in leds:
            self.__cube_view.set_led(led.x, led.y, led.z, led.state)
