# Real-Time ADC Data Visualizer

Программа для визуализации данных АЦП в реальном времени с микроконтроллера STM32 через последовательный порт.

## Возможности

- Отображение данных АЦП в реальном времени
- Настройка параметров подключения (порт, скорость передачи)
- Регулировка масштаба и смещения графика
- Управление процессом отображения (старт, пауза, остановка)
- Автоматическое масштабирование графика

## Требования

- Python 3.7+
- Установленные библиотеки (см. раздел "Установка")

## Установка

1. Установите Python 3.7 или новее с официального сайта: [python.org](https://www.python.org/downloads/)
2. Скачайте зависимости, выполнив команду: `pip install -r requirements.txt`
   Или используйте `install_dependencies.bat` (для Windows)
3. Запустите программу: `python Graph.py`

## Использование

1. Выберите последовательный порт из списка
2. Установите параметры:
- Размер буфера
- Опорное напряжение
- Разрядность АЦП
3. Нажмите кнопку "Play" для начала отображения данных
4. Используйте элементы управления для настройки графика:
- Масштаб по осям X/Y
- Смещение по оси Y
- Кнопки паузы и остановки

## Подключение к STM32

Программа ожидает данные в следующем формате:
- 3 байта на одно значение АЦП
- Первый бит первого байта - старший бит значения
- Последний бит третьего байта - младший бит значения

Пример кода для STM32 (HAL):
```c
uint16_t adc_value = HAL_ADC_GetValue(&hadc1);
uint8_t data[3];
HAL_UART_Transmit(&huart1, data, 3, HAL_MAX_DELAY);