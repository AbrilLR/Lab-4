# Señales electromiográficas EMG
## Descripción 
La electromiografía de superficie (sEMG) es una técnica no invasiva que permite registrar la actividad eléctrica generada por los músculos durante la contracción voluntaria. Esta señal refleja la activación de unidades motoras y puede ser utilizada para evaluar el comportamiento muscular bajo diferentes condiciones, como la aparición de fatiga.

En esta práctica se busca evaluar experimentalmente el fenómeno de la fatiga muscular mediante el registro y análisis de señales EMG en el músculo del antebrazo, durante una contracción repetitiva y constante de 30 segundos. A lo largo de este tiempo, se observarán variaciones en la amplitud y el contenido frecuencial de la señal, características típicas del proceso de fatiga.

Para poder analizar la señal EMG, se implementa el uso de filtros digitales para eliminar el ruido. Además, se utiliza aventanamiento para dividir la señal en segmentos temporales sobre los que se aplica el análisis, permitiendo observar la evolución temporal de sus características. Finalmente, se realiza un análisis espectral mediante la Transformada Rápida de Fourier (FFT), con el fin de estudiar cómo cambia el contenido en frecuencia a lo largo del tiempo, lo cual puede indicar si hay fatiga muscular.

## Captura de la señal
Para el proceso de adquisición de la señal de electromiografía seleccionamos el músculo del antebrazo, en este se colocaron los electrodos siendo dos de ellos electrodos activos y un electrodo de tierra.
Los electrodos fueron conectados al módulo de electromiografía AD8232, el cual actúa como un sistema de amplifiacación y filtrado de la señal.
Se connectó el módulo de electromiografia al modulo de adquisición de datos NI-DAQ el cual permite la adqusición de datos de la señal de EMG.
Con el siguiente código se estableció una frecuencia de muestreo de 1000 Hz, ya que la señal máxima de una electromiografiía, utilizando una frecuencia de muestreo de 1000 Hz aseguramos el cumplimiento teorema de Nyquist. El código también permite graficar y guardar los datos de la señal en un archivo CSV para su posterior análisis.

```python
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

```
![image](https://github.com/user-attachments/assets/2e2493f3-a1f1-4f9d-8cec-17b1703867c7)

La captura durante 30 segundos con el módulo de electromiografia dió como resultado la siguente señal

![emg](https://github.com/user-attachments/assets/62e6fe40-d95b-4216-8668-4e7759d804ff)


## Filtrado de la señal
Para eliminar componentes de la señal que no están relacionados con la actividad múscular se aplican dos tipos de filtros, un filtro pasa bajos atenua altas frecuencias que pueden corresponder a ruido electromagnético o interferencias y un filtro pasa altos para eliminar componentes de baja frecuencia, generalmente asociados a la linea base o al movimiento.

```python
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order)
    y = lfilter(b, a, data)
    return y

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a
def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order)
    y = lfilter(b, a, data)
    return y

filtered_signal_low = butter_lowpass_filter(emg_signal, high_cutoff, sampling_rate)
filtered_signal_band = butter_highpass_filter(filtered_signal_low, low_cutoff, sampling_rate)

```
![señalfil](https://github.com/user-attachments/assets/16f8cc78-984f-4097-a77e-5443b65000c4)

## Ventanamiento de la señal EMG
Para el analisis de los pulsos generados por contracción muscular se pidió al sujeto de prueba que hiciera contracciones de manera periodica durante 30 segundos, esto nos permite analizar la señal de manera más facil, esta se divide en ventanas para analizar cada contracción individualmente, para esto se aplica una ventana Hamming en vez de una Hanning, debido a que reduce las fugas espectrales, tiene mejor supresión de lobulos laterales, y es mejor para señales periodicas, cada vetana se aplica en un periodo de aproximadamente 682ms para 44 ventanas, correspondiente a las 44 contracciones que se hicieron en 30 segundos. Posteriormente se aplica transformada de fourier (FFT) y tambien se calcula y gráfica la densidad espectral de potencia, por propositos de facilidad solo se mostrarán las ventanas 1, 22 y 44, además se calcula la frecuencia media, mediana y desviación estandar para cada una de las ventanas.

```
# Parámetros de ventana
window_size = int(0.682 * sampling_rate)  # 682 ms
step_size = window_size  # Ventanas sin solapamiento
num_windows = len(filtered_signal) // step_size

plt.figure(figsize=(12, 6))
plt.plot(t, filtered_signal, label="Señal Filtrada")
plt.xlabel("Tiempo (s)")
plt.ylabel("Amplitud")
plt.title("Señal EMG Filtrada con Ventaneo")
plt.legend()
plt.show()

# Procesar cada ventana y calcular FFT 
for i in range(num_windows):
    start = i * step_size
    end = start + window_size
    if end > len(filtered_signal):
        break
    
    windowed_signal = filtered_signal[start:end] * np.hamming(window_size)
    freq_values = np.fft.fftfreq(window_size, d=dt)[:window_size // 2]
    fft_values = np.abs(fft(windowed_signal))[:window_size // 2]
    
    # Calcular densidad espectral de potencia (PSD)
    f_psd, Pxx = welch(windowed_signal, fs=sampling_rate, nperseg=window_size)
    
    # Calcular métricas
    freq_mean = np.sum(f_psd * Pxx) / np.sum(Pxx)  # Frecuencia media
    freq_median = f_psd[np.argmax(np.cumsum(Pxx) >= np.sum(Pxx) / 2)]  # Frecuencia mediana
    freq_std = np.sqrt(np.sum(Pxx * (f_psd - freq_mean) ** 2) / np.sum(Pxx))  # Desviación estándar
    
    print(f"Ventana {i+1} - Frecuencia Media: {freq_mean:.2f} Hz, Mediana: {freq_median:.2f} Hz, Desviación estándar: {freq_std:.2f} Hz")
    
    # Graficar espectro de frecuencias
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(freq_values, fft_values)
    plt.xlabel("Frecuencia (Hz)")
    plt.ylabel("Magnitud")
    plt.title(f"Espectro de Frecuencia - Ventana {i+1}")
    
    # Graficar densidad espectral de potencia
    plt.subplot(1, 2, 2)
    plt.semilogy(f_psd, Pxx)
    plt.xlabel("Frecuencia (Hz)")
    plt.ylabel("PSD")
    plt.title(f"Densidad Espectral de Potencia - Ventana {i+1}")
    
    plt.tight_layout()
    plt.show()

```
![Figure_1](https://github.com/user-attachments/assets/e379413e-a90a-43b0-8f14-373a09b0c639)
![Figure_2](https://github.com/user-attachments/assets/8c510731-03c1-4639-a1ba-02fd801ebd6c)
![Figure_3](https://github.com/user-attachments/assets/05e78778-aa84-4043-bfd1-cc86411b5e3d)

Al observar los espectros de frecuencia se puede observar como a medida que progresan las contracciones la magnitud de las frecuencias altas disminuye mientras que la de las frecuencias bajas aumenta, por lo que la densidad espectral de potencia disminuye, por lo que la señal tiene menos potencia, como es esperable al haber fatiga en el musculo, por lo que el método para dividir la señal considerandola como periodica es funcional, y se puede observar la progresión de la fatiga al realizar repetidamente un mismo movimiento, a continuación, los estadisticos obtenidos:
Ventana 1 - Frecuencia Media: 149.90 Hz, Mediana: 140.96 Hz, Desviación estándar: 87.30 Hz
Ventana 2 - Frecuencia Media: 148.98 Hz, Mediana: 133.62 Hz, Desviación estándar: 98.85 Hz
Ventana 3 - Frecuencia Media: 142.56 Hz, Mediana: 135.09 Hz, Desviación estándar: 88.34 Hz
Ventana 4 - Frecuencia Media: 154.44 Hz, Mediana: 133.62 Hz, Desviación estándar: 107.00 Hz
Ventana 5 - Frecuencia Media: 154.44 Hz, Mediana: 129.22 Hz, Desviación estándar: 97.15 Hz
Ventana 6 - Frecuencia Media: 154.07 Hz, Mediana: 136.56 Hz, Desviación estándar: 106.75 Hz
Ventana 7 - Frecuencia Media: 120.68 Hz, Mediana: 110.13 Hz, Desviación estándar: 87.87 Hz
Ventana 8 - Frecuencia Media: 124.82 Hz, Mediana: 98.38 Hz, Desviación estándar: 94.55 Hz
Ventana 9 - Frecuencia Media: 141.78 Hz, Mediana: 121.88 Hz, Desviación estándar: 97.17 Hz
Ventana 10 - Frecuencia Media: 155.31 Hz, Mediana: 135.09 Hz, Desviación estándar: 110.37 Hz
Ventana 11 - Frecuencia Media: 141.99 Hz, Mediana: 118.94 Hz, Desviación estándar: 92.02 Hz
Ventana 12 - Frecuencia Media: 142.36 Hz, Mediana: 111.60 Hz, Desviación estándar: 97.76 Hz
Ventana 13 - Frecuencia Media: 147.86 Hz, Mediana: 120.41 Hz, Desviación estándar: 99.15 Hz
Ventana 14 - Frecuencia Media: 119.79 Hz, Mediana: 104.25 Hz, Desviación estándar: 85.48 Hz
Ventana 15 - Frecuencia Media: 153.57 Hz, Mediana: 149.77 Hz, Desviación estándar: 85.60 Hz
Ventana 16 - Frecuencia Media: 144.04 Hz, Mediana: 126.28 Hz, Desviación estándar: 90.97 Hz
Ventana 17 - Frecuencia Media: 164.68 Hz, Mediana: 142.43 Hz, Desviación estándar: 103.72 Hz
Ventana 18 - Frecuencia Media: 119.88 Hz, Mediana: 96.91 Hz, Desviación estándar: 91.84 Hz
Ventana 19 - Frecuencia Media: 120.09 Hz, Mediana: 96.91 Hz, Desviación estándar: 83.94 Hz
Ventana 20 - Frecuencia Media: 133.38 Hz, Mediana: 99.85 Hz, Desviación estándar: 107.79 Hz
Ventana 21 - Frecuencia Media: 120.14 Hz, Mediana: 105.72 Hz, Desviación estándar: 88.01 Hz
Ventana 22 - Frecuencia Media: 136.69 Hz, Mediana: 121.88 Hz, Desviación estándar: 90.74 Hz
Ventana 23 - Frecuencia Media: 121.28 Hz, Mediana: 101.32 Hz, Desviación estándar: 94.75 Hz
Ventana 24 - Frecuencia Media: 114.61 Hz, Mediana: 95.44 Hz, Desviación estándar: 78.11 Hz
Ventana 25 - Frecuencia Media: 126.15 Hz, Mediana: 104.25 Hz, Desviación estándar: 89.21 Hz
Ventana 26 - Frecuencia Media: 105.06 Hz, Mediana: 92.51 Hz, Desviación estándar: 75.14 Hz
Ventana 27 - Frecuencia Media: 118.82 Hz, Mediana: 93.98 Hz, Desviación estándar: 81.60 Hz
Ventana 28 - Frecuencia Media: 122.94 Hz, Mediana: 104.25 Hz, Desviación estándar: 87.02 Hz
Ventana 29 - Frecuencia Media: 112.37 Hz, Mediana: 101.32 Hz, Desviación estándar: 82.63 Hz
Ventana 30 - Frecuencia Media: 102.77 Hz, Mediana: 83.70 Hz, Desviación estándar: 78.56 Hz
Ventana 31 - Frecuencia Media: 129.29 Hz, Mediana: 98.38 Hz, Desviación estándar: 94.17 Hz
Ventana 32 - Frecuencia Media: 122.69 Hz, Mediana: 108.66 Hz, Desviación estándar: 84.83 Hz
Ventana 33 - Frecuencia Media: 116.57 Hz, Mediana: 101.32 Hz, Desviación estándar: 83.28 Hz
Ventana 34 - Frecuencia Media: 95.83 Hz, Mediana: 76.36 Hz, Desviación estándar: 76.98 Hz
Ventana 35 - Frecuencia Media: 112.33 Hz, Mediana: 101.32 Hz, Desviación estándar: 81.37 Hz
Ventana 36 - Frecuencia Media: 137.13 Hz, Mediana: 116.00 Hz, Desviación estándar: 82.73 Hz
Ventana 37 - Frecuencia Media: 131.63 Hz, Mediana: 111.60 Hz, Desviación estándar: 92.11 Hz
Ventana 38 - Frecuencia Media: 116.59 Hz, Mediana: 95.44 Hz, Desviación estándar: 74.73 Hz
Ventana 39 - Frecuencia Media: 108.96 Hz, Mediana: 92.51 Hz, Desviación estándar: 80.53 Hz
Ventana 40 - Frecuencia Media: 134.56 Hz, Mediana: 124.81 Hz, Desviación estándar: 86.44 Hz
Ventana 41 - Frecuencia Media: 110.90 Hz, Mediana: 89.57 Hz, Desviación estándar: 96.44 Hz
Ventana 42 - Frecuencia Media: 99.80 Hz, Mediana: 85.17 Hz, Desviación estándar: 80.17 Hz
Ventana 43 - Frecuencia Media: 128.98 Hz, Mediana: 104.25 Hz, Desviación estándar: 90.46 Hz
Ventana 44 - Frecuencia Media: 102.73 Hz, Mediana: 80.76 Hz, Desviación estándar: 82.55 Hz

Para el analisis de la fátiga, normalmente se usa la frecuencia mediana, debido a que en estadistica, cuando una distribución de datos se encuentra sesgada hacía un lateral, la mediana de la distribución de datos disminuye hacia esa misma dirección, además esta disminución de la mediana es consistente y proporcional, la media a pesar de que tambien disminuye es más sensible a artefactos y presencia de picos y frecuencias altas. Tomando la frecuencia mediana podemos observar una disminución considerable en la frecuencia mediana, que a pesar de tener su mayor disminución en la ventana 34 (probablemente debidoa que el ventaneo periodico puede dejar fuera ciertos valores) mantiene una relación consistente hasta el final, por que se puede concluir que la disminución de la frecuencia mediana claramente se relaciona con la fatiga en la señal emg, y es util a la hora de determinarla cuando el analisis visual o espectral no es suficiente para que la fatiga sea observable.
