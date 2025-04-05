import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from nptdms import TdmsFile
import nidaqmx
from nidaqmx.system import System
from nidaqmx.constants import AcquisitionType
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QMessageBox, QGroupBox
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class EMGApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Adquisición de EMG con DAQ")
        self.setGeometry(100, 100, 350, 250)

        # Colores de fondo
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        self.setPalette(palette)

        main_layout = QVBoxLayout()

        # Sección de selección de dispositivo
        group_dispositivos = QGroupBox("Dispositivos DAQ")
        layout_disp = QVBoxLayout()
        self.puertos_combo = QComboBox()
        layout_disp.addWidget(QLabel("Selecciona un dispositivo:"))
        layout_disp.addWidget(self.puertos_combo)
        self.boton_actualizar = QPushButton("Actualizar Puertos")
        layout_disp.addWidget(self.boton_actualizar)
        group_dispositivos.setLayout(layout_disp)
        main_layout.addWidget(group_dispositivos)

        # Sección de control
        group_control = QGroupBox("Control de adquisición")
        layout_ctrl = QHBoxLayout()
        self.boton_iniciar = QPushButton("Iniciar captura por 30 seg")
        self.boton_guardar = QPushButton("Guardar Señal")
        self.boton_mostrar = QPushButton("Mostrar Gráfica")
        layout_ctrl.addWidget(self.boton_iniciar)
        layout_ctrl.addWidget(self.boton_guardar)
        layout_ctrl.addWidget(self.boton_mostrar)
        group_control.setLayout(layout_ctrl)
        main_layout.addWidget(group_control)

        self.setLayout(main_layout)

        # Conectar botones
        self.boton_actualizar.clicked.connect(self.actualizar_puertos)
        self.boton_iniciar.clicked.connect(self.iniciar_adquisicion)
        self.boton_guardar.clicked.connect(self.guardar_senal)
        self.boton_mostrar.clicked.connect(self.mostrar_grafica)

        self.actualizar_puertos()

    def actualizar_puertos(self):
        self.puertos_combo.clear()
        try:
            system = System.local()
            dispositivos = system.devices
            if not dispositivos:
                QMessageBox.warning(self, "Error", "No se detectaron dispositivos DAQ.")
            else:
                for dispositivo in dispositivos:
                    self.puertos_combo.addItem(dispositivo.name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al obtener dispositivos DAQ:\n{e}")

    def iniciar_adquisicion(self):
        device_name = self.puertos_combo.currentText()
        if not device_name:
            QMessageBox.warning(self, "Error", "Selecciona un dispositivo DAQ antes de iniciar la adquisición.")
            return

        self.archivo_tdms = "TestData.tdms"
        self.duracion = 30  
        self.frecuencia_muestreo = 1000  
        total_muestras = self.duracion * self.frecuencia_muestreo

        try:
            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(f"{device_name}/ai0")
                task.timing.cfg_samp_clk_timing(
                    self.frecuencia_muestreo,
                    sample_mode=AcquisitionType.FINITE,
                    samps_per_chan=total_muestras
                )

                task.start()
                datos = task.read(number_of_samples_per_channel=total_muestras, timeout=nidaqmx.constants.WAIT_INFINITELY)
                task.stop()

            self.procesar_datos(datos)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error durante la adquisición de datos:\n{e}")

    def procesar_datos(self, datos):
        self.tiempos = np.linspace(0, len(datos) / self.frecuencia_muestreo, len(datos))
        self.valores = np.array(datos)
        self.mostrar_grafica()

    def mostrar_grafica(self):
        if not hasattr(self, 'tiempos') or not hasattr(self, 'valores') or len(self.tiempos) == 0:
            QMessageBox.warning(self, "Error", "No hay datos para graficar. Realiza una adquisición primero.")
            return

        plt.figure(figsize=(10, 5))
        plt.plot(self.tiempos, self.valores, label="Señal EMG", color="b", linestyle="dashed")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Voltaje (V)")
        plt.title("Señal EMG Adquirida")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.show()

    def guardar_senal(self):
        if not hasattr(self, 'tiempos') or not hasattr(self, 'valores') or len(self.tiempos) == 0:
            QMessageBox.warning(self, "Error", "No hay datos para guardar. Realiza una adquisición primero.")
            return
        
        datos = pd.DataFrame({"Tiempo (s)": self.tiempos, "Voltaje (V)": self.valores})
        archivo_csv = "senal_emg.csv"
        datos.to_csv(archivo_csv, index=False)
        QMessageBox.information(self, "Guardado", f"Señal guardada en {archivo_csv}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ventana = EMGApp()
    ventana.show()
    sys.exit(app.exec_())
