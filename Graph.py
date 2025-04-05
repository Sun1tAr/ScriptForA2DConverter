import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np
import sys
from serial.tools import list_ports

# Константы по умолчанию
DEFAULT_BUFFER_SIZE = 5000
DEFAULT_VREF = 3.3
DEFAULT_BITS = 10
DEFAULT_BAUDRATE = 115200


class RealTimePlot:
    def __init__(self):
        # Инициализация Qt приложения
        self.app = QtWidgets.QApplication(sys.argv)
        self.j = 0
        self.is_running = False
        self.is_paused = False
        self.serial_port = None

        # Создание главного окна
        self.main_window = QtWidgets.QWidget()
        self.main_window.setWindowTitle("STM32 Data Real-Time")
        self.main_window.resize(1000, 800)

        # Основной layout
        main_layout = QtWidgets.QVBoxLayout()
        self.main_window.setLayout(main_layout)

        # Панель инициализации
        init_panel = QtWidgets.QHBoxLayout()

        # Выбор порта
        port_label = QtWidgets.QLabel("Порт:")
        self.port_combo = QtWidgets.QComboBox()
        self.refresh_ports()

        # Размер буфера
        buffer_label = QtWidgets.QLabel("Размер буфера:")
        self.buffer_spin = QtWidgets.QSpinBox()
        self.buffer_spin.setRange(10, 10000)
        self.buffer_spin.setValue(DEFAULT_BUFFER_SIZE)

        # Опорное напряжение
        vref_label = QtWidgets.QLabel("Опорное напряжение (В):")
        self.vref_spin = QtWidgets.QDoubleSpinBox()
        self.vref_spin.setRange(0.1, 10.0)
        self.vref_spin.setValue(DEFAULT_VREF)
        self.vref_spin.setSingleStep(0.1)

        # Количество бит
        bits_label = QtWidgets.QLabel("Бит АЦП:")
        self.bits_spin = QtWidgets.QSpinBox()
        self.bits_spin.setRange(8, 16)
        self.bits_spin.setValue(DEFAULT_BITS)

        # Добавляем элементы на панель инициализации
        init_panel.addWidget(port_label)
        init_panel.addWidget(self.port_combo)
        init_panel.addWidget(buffer_label)
        init_panel.addWidget(self.buffer_spin)
        init_panel.addWidget(vref_label)
        init_panel.addWidget(self.vref_spin)
        init_panel.addWidget(bits_label)
        init_panel.addWidget(self.bits_spin)

        # Панель управления
        control_panel = QtWidgets.QHBoxLayout()

        # Кнопки управления
        self.play_btn = QtWidgets.QPushButton()
        self.play_btn.setIcon(self.app.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.play_btn.clicked.connect(self.start_plotting)

        self.pause_btn = QtWidgets.QPushButton()
        self.pause_btn.setIcon(self.app.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)

        self.stop_btn = QtWidgets.QPushButton()
        self.stop_btn.setIcon(self.app.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop_plotting)
        self.stop_btn.setEnabled(False)

        # Элементы управления масштабом по X
        x_scale_label = QtWidgets.QLabel("Масштаб X:")
        self.x_scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.x_scale_slider.setRange(1, 300)
        self.x_scale_slider.setValue(100)
        self.x_scale_value = QtWidgets.QLabel("100%")

        # Элементы управления масштабом по Y
        y_scale_label = QtWidgets.QLabel("Масштаб Y:")
        self.y_scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.y_scale_slider.setRange(1, 200)
        self.y_scale_slider.setValue(100)
        self.y_scale_value = QtWidgets.QLabel("100%")

        # Элементы управления смещением по Y
        y_offset_label = QtWidgets.QLabel("Смещение Y:")
        self.y_offset_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.y_offset_slider.setRange(-100, 100)
        self.y_offset_slider.setValue(0)
        self.y_offset_value = QtWidgets.QLabel("0%")

        # Кнопка авто масштабирования
        auto_scale_btn = QtWidgets.QPushButton("Автомасштаб")
        auto_scale_btn.clicked.connect(self.auto_scale)

        # Добавляем элементы на панель управления
        control_panel.addWidget(self.play_btn)
        control_panel.addWidget(self.pause_btn)
        control_panel.addWidget(self.stop_btn)
        control_panel.addWidget(x_scale_label)
        control_panel.addWidget(self.x_scale_slider)
        control_panel.addWidget(self.x_scale_value)
        control_panel.addWidget(y_scale_label)
        control_panel.addWidget(self.y_scale_slider)
        control_panel.addWidget(self.y_scale_value)
        control_panel.addWidget(y_offset_label)
        control_panel.addWidget(self.y_offset_slider)
        control_panel.addWidget(self.y_offset_value)
        control_panel.addWidget(auto_scale_btn)

        # Добавляем панели в основной layout
        main_layout.addLayout(init_panel)
        main_layout.addLayout(control_panel)

        # Создаем виджет графика
        self.win = pg.GraphicsLayoutWidget()
        main_layout.addWidget(self.win)

        # Настройка графика
        self.plot = self.win.addPlot()
        self.plot.setLabel('left', 'Напряжение', units='В')
        self.plot.setLabel('bottom', 'Время', units='')
        self.plot.setLabel
        self.plot.showGrid(x=True, y=True)

        # Инициализация данных (пока пустые)
        self.data = np.array([])
        self.curve = self.plot.plot([], pen='y')

        # Центральная линия (по середине между 0 и Vref)
        self.center_line = pg.InfiniteLine(
            angle=0,
            pos=DEFAULT_VREF / 2,
            pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine)
        )
        self.plot.addItem(self.center_line)

        # Начальные значения масштаба и смещения
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.y_offset = 0.0
        self.data_range = (0, DEFAULT_VREF)

        # Настройка таймера
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

        # Подключаем обработчики масштаба
        self.x_scale_slider.valueChanged.connect(self.update_x_scale)
        self.y_scale_slider.valueChanged.connect(self.update_y_scale)
        self.y_offset_slider.valueChanged.connect(self.update_y_offset)

        # Обновляем диапазон Y
        self.update_y_range()

        self.counter = 0
        self.main_window.show()

    def refresh_ports(self):
        """Обновление списка доступных портов"""
        self.port_combo.clear()
        ports = list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def start_plotting(self):
        """Запуск процесса отображения данных"""
        if self.is_running:
            return

        port = self.port_combo.currentText()
        buffer_size = self.buffer_spin.value()
        vref = self.vref_spin.value()
        bits = self.bits_spin.value()

        try:
            self.serial_port = serial.Serial(port, DEFAULT_BAUDRATE, timeout=1)
            print(f"Подключено к {port} на {DEFAULT_BAUDRATE} бод")

            # Инициализация данных
            self.data = np.zeros(buffer_size)
            self.curve.setData(self.data)

            # Обновляем центральную линию
            self.center_line.setPos(vref / 2)
            self.data_range = (0, vref)
            self.update_y_range()

            # Включаем кнопки управления
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

            # Запускаем таймер
            self.is_running = True
            self.is_paused = False
            self.timer.start(1)

        except serial.SerialException as e:
            print(f"Ошибка открытия порта: {e}")
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "Ошибка",
                f"Не удалось открыть порт {port}:\n{e}"
            )

    def toggle_pause(self):
        """Переключение режима паузы"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setIcon(self.app.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        else:
            self.pause_btn.setIcon(self.app.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

    def stop_plotting(self):
        """Остановка процесса отображения данных"""
        self.is_running = False
        self.timer.stop()

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        # Сбрасываем кнопки
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setIcon(self.app.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

        # Очищаем график
        self.data = np.array([])
        self.curve.setData(self.data)

    def update_x_scale(self):
        """Обновление масштаба по оси X"""
        self.x_scale = self.x_scale_slider.value() / 100.0
        self.x_scale_value.setText(f"{self.x_scale_slider.value()}%")
        self.plot.setXRange(0, len(self.data) * self.x_scale)

    def update_y_scale(self):
        """Обновление масштаба по оси Y"""
        self.y_scale = self.y_scale_slider.value() / 100.0
        self.y_scale_value.setText(f"{self.y_scale_slider.value()}%")
        self.update_y_range()

    def update_y_offset(self):
        """Обновление смещения по оси Y"""
        self.y_offset = self.y_offset_slider.value()
        self.y_offset_value.setText(f"{self.y_offset}%")
        self.update_y_range()

    def update_y_range(self):
        """Обновление диапазона по оси Y с учетом масштаба и смещения"""
        if hasattr(self, 'data_range'):
            min_val, max_val = self.data_range
            range_height = (max_val - min_val) * self.y_scale
            offset = (max_val + min_val) / 2 * (self.y_offset / 100)

            center = (max_val + min_val) / 2 + offset
            self.center_line.setPos(center)

            self.plot.setYRange(center - range_height / 2, center + range_height / 2)

    def auto_scale(self):
        """Автоматическое масштабирование"""
        if len(self.data) > 0:
            min_val = min(self.data)
            max_val = max(self.data)
            margin = (max_val - min_val) * 0.1  # 10% отступ

            self.data_range = (min_val - margin, max_val + margin)
            self.y_scale_slider.setValue(100)
            self.y_offset_slider.setValue(0)
            self.update_y_range()
            self.plot.setXRange(0, len(self.data))
            self.x_scale_slider.setValue(100)

    def update(self):
        if not self.is_running or self.is_paused:
            return

        try:
            # Чтение 3 байт из последовательного порта
            b = self.serial_port.read(3)
            if len(b) == 3:
                # Преобразование 3 байт в 10-битное значение
                value = ((b[0] & 1) << 9) | (b[1] << 1) | ((b[2] >> 7) & 1)

                # Обновление данных
                self.data[:-1] = self.data[1:]  # Сдвиг данных влево
                self.data[-1] = value * self.vref_spin.value() / (2 ** self.bits_spin.value())

                # Обновление графика
                self.curve.setData(self.data)

                # Периодический вывод в консоль для отладки
                self.counter += 1
                if self.counter % 200 == 0:
                    print(f"Текущее значение: {self.data[-1]:.3f} В")

        except Exception as e:
            print(f"Ошибка чтения данных: {e}")
            self.stop_plotting()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    plotter = RealTimePlot()
    plotter.run()