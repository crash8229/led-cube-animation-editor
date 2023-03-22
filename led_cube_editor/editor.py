import operator
from copy import deepcopy
from functools import reduce
from math import ceil
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from qtpy.QtCore import Signal, Qt, QRect, QSize, QPoint
from qtpy.QtWidgets import *
from qtpy import QtGui

from led_cube_editor import __version__
from led_cube_view import LEDCubeView  # type:ignore
from qtpy_led import Led  # type:ignore


class HSpacer(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.HLine)


class VSpacer(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.VLine)


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
    duration_changed: Signal = Signal(int)  # type: ignore
    display_mode_changed: Signal = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # super().__init__("Editor Options", parent)  # type: ignore
        super().__init__("", parent)  # type: ignore
        self._layout: QHBoxLayout = QHBoxLayout(self)  # type: ignore

        ## View Box Buttons ##
        view_buttons = QVBoxLayout()
        self._layout.addLayout(view_buttons)
        view_full: QPushButton = QPushButton("Show Full Cube", self)
        view_layer: QPushButton = QPushButton("Show Active Layer", self)
        view_buttons.addWidget(view_full)
        view_buttons.addWidget(view_layer)
        view_full.clicked.connect(lambda: self.display_mode_changed.emit(0))  # type: ignore
        view_layer.clicked.connect(lambda: self.display_mode_changed.emit(1))  # type: ignore

        ## Spacer ##
        self._layout.addWidget(VSpacer(self))

        ## Frame Options ##
        frame_options = QVBoxLayout()
        self._layout.addLayout(frame_options)
        # Frame Selector
        frame_selector = QWidget(self)
        frame_selector_lo = QVBoxLayout(frame_selector)  # type: ignore

        self.__frame_menu_up_button: QPushButton = QPushButton("⟰", frame_selector)
        self.__frame_menu: QComboBox = QComboBox(frame_selector)
        self.__frame_menu_down_button: QPushButton = QPushButton("⟱", frame_selector)

        frame_selector_lo.addWidget(self.__frame_menu_up_button)
        frame_selector_lo.addWidget(self.__frame_menu)
        frame_selector_lo.addWidget(self.__frame_menu_down_button)

        self.__frame_menu_up_button.clicked.connect(  # type: ignore
            lambda x: self.__button_change_menu(self.__frame_menu, True))
        self.__frame_menu_down_button.clicked.connect(  # type: ignore
            lambda x: self.__button_change_menu(self.__frame_menu, False))
        self.__frame_menu.currentIndexChanged.connect(  # type: ignore
            lambda x: self.__update_button_states(self.__frame_menu, self.__frame_menu_up_button,
                                                  self.__frame_menu_down_button))
        self.__frame_menu.currentIndexChanged.connect(self.frame_changed)  # type: ignore

        self.__update_button_states(
            self.__frame_menu, self.__frame_menu_up_button, self.__frame_menu_down_button
        )

        frame_selector_with_label = WidgetWithLabel(
            frame_selector, "Frame:", "left", self
        )
        frame_options.addWidget(frame_selector_with_label)

        # Frame Duration
        self.__frame_duration: QSpinBox = QSpinBox(frame_selector)
        self.__frame_duration.setRange(0, 65535)
        self.__frame_duration.setValue(5)
        self.__frame_duration.valueChanged.connect(self.duration_changed)  # type: ignore
        frame_options.addWidget(WidgetWithLabel(self.__frame_duration, "Duration (ms):", "left", self))

        ## Spacer ##
        self._layout.addWidget(VSpacer(self))

        ## Layer Selector ##
        layer_selector = QWidget(self)

        layer_selector_lo = QVBoxLayout(layer_selector)  # type: ignore
        self.__layer_menu_up_button: QPushButton = QPushButton("⟰", layer_selector)
        self.__layer_menu: QComboBox = QComboBox(layer_selector)
        self.__layer_menu_down_button: QPushButton = QPushButton("⟱", layer_selector)

        layer_selector_lo.addWidget(self.__layer_menu_up_button)
        layer_selector_lo.addWidget(self.__layer_menu)
        layer_selector_lo.addWidget(self.__layer_menu_down_button)

        self.__layer_menu_up_button.clicked.connect(  # type: ignore
            lambda x: self.__button_change_menu(self.__layer_menu, True))
        self.__layer_menu_down_button.clicked.connect(  # type: ignore
            lambda x: self.__button_change_menu(self.__layer_menu, False))
        self.__layer_menu.currentIndexChanged.connect(  # type: ignore
            lambda x: self.__update_button_states(self.__layer_menu, self.__layer_menu_up_button,
                                                  self.__layer_menu_down_button))
        self.__layer_menu.currentIndexChanged.connect(self.layer_changed)  # type: ignore

        self.__update_button_states(
            self.__layer_menu, self.__layer_menu_up_button, self.__layer_menu_down_button
        )

        layer_selector_with_label = WidgetWithLabel(
            layer_selector, "Layer:", "left", self
        )
        layer_selector_with_label.label.setStyleSheet(
            "QLabel { background-color: green; color: white }"
        )
        self._layout.addWidget(layer_selector_with_label)

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
            up_button.clearFocus()
            up_button.setEnabled(False)
        else:
            up_button.setEnabled(True)
        if idx <= 0:
            down_button.clearFocus()
            down_button.setEnabled(False)
        else:
            down_button.setEnabled(True)

    def set_layers(self, number: int) -> None:
        self.__layer_menu.clear()
        for i in range(number):
            self.__layer_menu.addItem(f"{i + 1:02d}")
        self.__update_button_states(
            self.__layer_menu, self.__layer_menu_up_button, self.__layer_menu_down_button
        )

    def set_frames(self, number: int) -> None:
        self.__frame_menu.clear()
        for i in range(number):
            self.__frame_menu.addItem(f"{i + 1:02d}")
        self.__update_button_states(
            self.__frame_menu, self.__frame_menu_up_button, self.__frame_menu_down_button
        )

    def set_duration(self, ms: int) -> None:
        self.__frame_duration.valueChanged.disconnect(self.duration_changed)  # type: ignore
        self.__frame_duration.setValue(ms)
        self.__frame_duration.valueChanged.connect(self.duration_changed)  # type: ignore


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

    def __init__(self, parent: Optional[QWidget], x: int, y: int, z: int, duration: int = 5) -> None:
        super().__init__(parent)
        self.__setup_layers(x, y, z)
        self.__duration = 5
        self.__version = 1
        self.__type = 1

        # V1 specific variables
        self.duration = duration

    def __setup_layers(self, x: int, y: int, z: int) -> None:
        for z_num in range(z):
            layer = Layer(self, x, y, z_num)
            layer.led_changed.connect(self.led_changed)
            self.addWidget(layer)

    def change_layer(self, idx: int) -> None:
        self.setCurrentIndex(idx)

    def get_layers(self) -> Tuple[Layer, ...]:
        return tuple(self.widget(i) for i in range(self.count()))  # type: ignore

    @property
    def current_layer(self) -> Layer:
        return self.currentWidget()  # type: ignore

    @property
    def current_layer_idx(self) -> int:
        return self.currentIndex()

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
    frame_changed: Signal = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # super().__init__("Layer Editor", parent)  # type: ignore
        super().__init__("", parent)  # type: ignore
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)  # type: ignore

        self.__rubberband: QRubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.__rubberband_origin: QPoint = QPoint()
        self.__selected_leds: Tuple[LEDWithPosition, ...] = tuple()

        self._layout: QStackedLayout = QStackedLayout(self)  # type: ignore

    @property
    def current_frame(self) -> Frame:
        return self._layout.currentWidget()  # type: ignore

    def change_frame(self, idx: int) -> None:
        if self._layout.count() <= idx < 0:
            raise ValueError("Out of range")

        frame: Frame = self._layout.currentWidget()  # type: ignore
        try:
            frame.led_changed.disconnect(self.led_changed)
        except RuntimeError:
            pass

        self._layout.setCurrentIndex(idx)

        frame: Frame = self._layout.widget(idx)  # type: ignore
        frame.led_changed.connect(self.led_changed)
        self.frame_changed.emit(idx)

    def change_layer(self, idx: int) -> None:
        frame: Frame = self._layout.currentWidget()  # type: ignore
        frame.change_layer(idx)

    def change_duration(self, ms: int) -> None:
        frame: Frame = self._layout.currentWidget()  # type: ignore
        frame.duration = ms

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
        # TODO: Figure out how to select the LEDs under the rubberband
        # x1: int
        # y1: int
        # x2: int
        # y2: int
        # rect = self.__rubberband.geometry()
        # x1, y1, x2, y2 = rect.getCoords()  # type: ignore
        # x1, y1 = self.__rubberband.mapToGlobal(QPoint(x1, y1)).toTuple()  # type: ignore
        # x2, y2 = self.__rubberband.mapToGlobal(QPoint(x2, y2)).toTuple()  # type: ignore
        # leds = self.current_frame.current_layer.get_leds()
        # for led in leds:
        #     x, y = led.mapToGlobal(led.pos()).toTuple()
        #     if x1 <= x <= x2 and y1 <= y <= y2:
        #         led.set_status(not led.state)

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
        self.change_frame(self._layout.currentIndex())


class AnimationSettings(QVBoxLayout):
    __cube_size_changed: Signal = Signal()  # type: ignore

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__()

        ## V1 Specific ##
        self.v1_specific = QGroupBox("Animation Options", parent)  # type: ignore
        self.addWidget(self.v1_specific)
        v1_specific_lo = QFormLayout(self.v1_specific)

        # Variables
        self.__animation_settings: Dict[str, Any] = {
            "name": "",
            "tlc_count": 0
        }

        # Widgets
        self.__name_field = QLineEdit(self.__animation_settings["name"], parent)
        self.__name_field.setMaxLength(32)
        self.__name_field.textChanged.connect(lambda x: self.__update_animation_setting("name", x))  # type: ignore
        v1_specific_lo.addRow("Name:", self.__name_field)

        # Signals
        self.__cube_size_changed.connect(self.__update_tlc_count)

        ## Cube Settings ##
        self.cube_specific = QGroupBox("LED Cube Options", parent)  # type: ignore
        self.addWidget(self.cube_specific)
        cube_specific_lo = QFormLayout(self.cube_specific)

        # Variables
        self.__led_cube_settings: Dict[str, Any] = {
            "dimension": [5, 5, 5],
            "off_color": [0, 0, 0, 0],
            "on_color": [1, 0, 0, 1],
        }

        # Widgets
        self.__x_dimension = QSpinBox(parent)
        self.__x_dimension.setRange(2, 16)
        self.__x_dimension.setValue(self.__led_cube_settings["dimension"][0])
        label = QLabel("Number of LEDs on X Axis:", parent)  # type: ignore
        label.setStyleSheet(
            "QLabel { background-color: blue; color: white }"
        )
        cube_specific_lo.addRow(label, self.__x_dimension)

        self.__y_dimension = QSpinBox(parent)
        self.__y_dimension.setRange(2, 16)
        self.__y_dimension.setValue(self.__led_cube_settings["dimension"][1])
        label = QLabel("Number of LEDs on Y Axis:", parent)  # type: ignore
        label.setStyleSheet(
            "QLabel { background-color: yellow; color: black }"
        )
        cube_specific_lo.addRow(label, self.__y_dimension)

        self.__z_dimension = QSpinBox(parent)
        self.__z_dimension.setRange(2, 16)
        self.__z_dimension.setValue(self.__led_cube_settings["dimension"][2])
        label = QLabel("Number of LEDs on Z Axis:", parent)  # type: ignore
        label.setStyleSheet(
            "QLabel { background-color: green; color: white }"
        )
        cube_specific_lo.addRow(label, self.__z_dimension)

        # Signals
        self.__x_dimension.valueChanged.connect(lambda x: self.__update_cube_size(0, x))  # type: ignore
        self.__y_dimension.valueChanged.connect(lambda x: self.__update_cube_size(1, x))  # type: ignore
        self.__z_dimension.valueChanged.connect(lambda x: self.__update_cube_size(2, x))  # type: ignore

        self.__cube_size_changed.emit()

    @property
    def cube_settings(self) -> Dict[str, Any]:
        return deepcopy(self.__led_cube_settings)

    def set_cube_setting_state(self, state: bool) -> None:
        self.cube_specific.setEnabled(state)
        if state:
            self.cube_specific.show()
        else:
            self.cube_specific.hide()

    def __update_cube_size(self, axis: int, dimension: int) -> None:
        self.__led_cube_settings["dimension"][axis] = dimension
        self.__cube_size_changed.emit()

    @property
    def animation_settings(self) -> Dict[str, Any]:
        return deepcopy(self.__animation_settings)

    def __update_animation_setting(self, key: str, value: Any) -> None:
        if key not in self.__animation_settings:
            raise KeyError(f"{key} not found in animation settings")
        self.__animation_settings[key] = value

    def __update_tlc_count(self) -> None:
        cube_dimensions = self.__led_cube_settings["dimension"]
        self.__update_animation_setting(
            "tlc_count",
            ceil((reduce(operator.mul, cube_dimensions[:2], 1) + cube_dimensions[2]) / 16)
        )


class LEDCubeEditor(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"LED Cube Editor {__version__}")
        self.setWindowIcon(QtGui.QIcon(str(Path(__file__).resolve().parent.joinpath("icon.png"))))  # type: ignore
        main_widget = QWidget(self)
        main_layout: QGridLayout = QGridLayout(main_widget)
        main_widget.setLayout(main_layout)
        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)  # type: ignore
        self.setCentralWidget(main_widget)

        ## Variables ##
        self.__display_mode: int = 0

        ## Menu ##
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        menu = QMenu("File", menubar)  # type: ignore
        actions: List[QAction] = list()
        actions.append(QAction("New", menu))
        actions[-1].triggered.connect(self.__file_new)  # type: ignore
        actions.append(QAction("Open", menu))
        actions[-1].triggered.connect(self.__file_open)  # type: ignore
        actions.append(QAction("Save", menu))
        actions[-1].triggered.connect(self.__file_save)  # type: ignore
        actions[-1].setEnabled(False)
        actions.append(QAction("Save as", menu))
        actions[-1].triggered.connect(self.__file_save_as)  # type: ignore
        actions[-1].setEnabled(False)
        actions.append(QAction("Exit", menu))
        actions[-1].triggered.connect(self.close)  # type: ignore
        for a in actions:
            menu.addAction(a)
        menubar.addMenu(menu)

        menu = QMenu("View", menubar)  # type: ignore
        actions = list()
        actions.append(QAction("Show Library Panel", menu))
        actions[-1].triggered.connect(self.__view_library_panel)  # type: ignore
        actions[-1].setCheckable(True)
        for a in actions:
            menu.addAction(a)
        menubar.addMenu(menu)

        menu = QMenu("Animation", menubar)  # type: ignore
        actions = list()
        actions.append(QAction("Animation Setup", menu))
        actions[-1].triggered.connect(self.__animation_setup)  # type: ignore
        for a in actions:
            menu.addAction(a)
        menubar.addMenu(menu)

        ## Widget Setup ##
        # Stylesheet for QGroupbox
        # self.setStyleSheet(
        #     "QGroupBox { border: 1px solid black; border-radius: 5px; margin-top: 3ex; }"
        #     "\nQGroupBox::title { subcontrol-position: top center; subcontrol-origin: margin; }"
        # )

        # Grid Stretch
        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(0, 10)
        main_layout.setColumnStretch(1, 12)

        # LED Editor Controls
        self.__editor_controls = EditorControls(self)
        self.__editor_controls.setEnabled(False)
        main_layout.addWidget(self.__editor_controls, 0, 0, 1, 2)

        # LED Layer Edit
        self.__led_editor = LEDLayerEditor(parent=main_widget)
        main_layout.addWidget(self.__led_editor, 1, 1, 3, 1)
        self.__led_editor.setMinimumSize(450, 450)  # type: ignore
        self.__editor_controls.layer_changed.connect(self.__led_editor.change_layer)
        self.__editor_controls.frame_changed.connect(self.__led_editor.change_frame)
        self.__editor_controls.duration_changed.connect(self.__led_editor.change_duration)
        self.__led_editor.frame_changed.connect(self.__update_frame_duration_control)

        # Cube View Controls
        # cube_controls = QGroupBox("View Box Options", main_widget)  # type: ignore
        # cube_controls_lo = QVBoxLayout()
        # cube_controls.setLayout(cube_controls_lo)
        # main_layout.addWidget(cube_controls, 0, 1, 1, 1)

        # Cube View
        self.__cube_view = LEDCubeView(main_widget)
        main_layout.addWidget(self.__cube_view, 1, 0, 3, 1)
        self.__config_list = self.__cube_view.config_list()
        self.__led_editor.led_changed.connect(self.__cube_view.set_led)
        self.__cube_view.setMinimumSize(550, 450)
        self.__led_editor.frame_changed.connect(self.__set_frame_view)
        self.__editor_controls.display_mode_changed.connect(self.__change_display_mode)
        self.__editor_controls.layer_changed.connect(self.__update_layer_view)
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

    #### Menu Actions ####
    ## File Menu ##
    def __file_new(self) -> None:
        raise NotImplementedError

    def __file_open(self) -> None:
        raise NotImplementedError

    def __file_save(self) -> None:
        raise NotImplementedError

    def __file_save_as(self) -> None:
        raise NotImplementedError

    ## View Menu ##
    def __view_library_panel(self, checked: bool) -> None:
        raise NotImplementedError

    ## Animation Menu ##
    def __animation_setup(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Animation Setup")
        dialog.setMinimumWidth(320)
        # dialog.resize(dialog.minimumWidth(), dialog.height())  # type: ignore
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        settings = AnimationSettings()
        settings.set_cube_setting_state(False)
        layout.addLayout(settings)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)  # type: ignore
        buttons.accepted.connect(dialog.accept)  # type: ignore
        buttons.rejected.connect(dialog.reject)  # type: ignore
        layout.addWidget(buttons)

        result = dialog.exec()
        dialog.deleteLater()
        if result:
            print(settings.animation_settings)
            print(settings.cube_settings)
            raise NotImplementedError

    #### Events ####
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        close = QMessageBox()  # type: ignore
        close.setText("Are you sure you want to quit?")
        close.setWindowTitle("Exit")
        close.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        response: int = close.exec()

        if response == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    #### Slots ####
    def __set_frame_view(self, idx: int) -> None:
        leds: Tuple[LEDWithPosition, ...] = tuple(
            led
            for layer in self.__led_editor.get_frame(idx).get_layers()
            for led in layer.get_leds()
        )
        for led in leds:
            self.__cube_view.set_led(led.x, led.y, led.z, led.state)

    def __update_frame_duration_control(self, idx: int) -> None:
        self.__editor_controls.set_duration(self.__led_editor.get_frame(idx).duration)

    def __change_display_mode(self, mode: int) -> None:
        if mode == 0:
            self.__display_mode = 0
            self.__cube_view.show_cube()
        elif mode == 1:
            self.__display_mode = 1
            self.__update_layer_view()

    #### Methods ####
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
        self.__editor_controls.setEnabled(True)

    def __update_layer_view(self) -> None:
        if self.__display_mode != 0:
            self.__cube_view.show_layer(self.__led_editor.current_frame.current_layer_idx)
