import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
import sys

# Настройки последовательного порта
PORT = 'COM5'
BAUDRATE = 115200
BUFFER_SIZE = 500  # Размер буфера для отображения
Vref = 3.3          # Опорное напряжение, В
N = 10              # Количество бит PayLoad на MISO за такт


class RealTimePlot:
    def __init__(self):
        # Инициализация Qt приложения
        self.app = QtWidgets.QApplication(sys.argv)
        self.j = 0
        # Создание окна для графика
        self.win = pg.GraphicsLayoutWidget(title="STM32 Data Real-Time")
        self.win.resize(800, 600)

        # Настройка графика
        self.plot = self.win.addPlot()
        self.plot.setLabel('left', 'Значение АЦП', units='o.e.')
        self.plot.setLabel('bottom', 'Время', units='отсчёты')
        self.plot.showGrid(x=True, y=True)

        # Инициализация данных
        self.data = np.zeros(BUFFER_SIZE)
        self.curve = self.plot.plot(self.data, pen='y')

        # Настройка последовательного порта
        try:
            self.serial_port = serial.Serial(PORT, BAUDRATE, timeout=1)
            print(f"Подключено к {PORT} на {BAUDRATE} бод")
        except serial.SerialException as e:
            print(f"Ошибка открытия порта: {e}")
            sys.exit(1)

        # Таймер для обновления графика
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1)  # Обновление каждые 1 мс

        self.counter = 0
        self.win.show()

    def update(self):
        try:
            # Чтение 3 байт из последовательного порта
            b = self.serial_port.read(3)
            if len(b) == 3:
                # Преобразование 3 байт в 10-битное значение (исправленная строка)
                value = ((b[0] & 1) << 9) | (b[1] << 1) | ((b[2] >> 7) & 1)

                if self.j < 3:
                    self.j += 1
                else:
                    self.j = 0
                if self.j == 0:
                    # Обновление данных
                    self.data[:-1] = self.data[1:]  # Сдвиг данных влево
                    self.data[-1] = value * Vref / 2**N  # Добавление нового значения

                    # Обновление графика
                    self.curve.setData(self.data)

                # Периодический вывод в консоль для отладки
                self.counter += 1
                if self.counter % 200 == 0:
                    print(f"Текущее значение: {value * Vref / 2**N}")

        except Exception as e:
            print(f"Ошибка чтения данных: {e}")

    def run(self):
        sys.exit(self.app.exec_())


# Запуск приложения
if __name__ == '__main__':
    plotter = RealTimePlot()
    plotter.run()