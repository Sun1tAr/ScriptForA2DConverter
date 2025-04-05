### install_dependencies.bat

@echo off
:: Batch file for installing Python dependencies for Real-Time ADC Visualizer

echo Installing required Python packages...
echo.


:: Install packages
python -m pip install --upgrade pip
python -m pip install pyserial pyqtgraph numpy

echo.
echo Installation complete!
echo You can now run the program with: python Graph.py
pause