import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.signal as signal
from scipy.signal import butter, lfilter, welch
from scipy.fftpack import fft
from scipy.stats import ttest_ind

# Funciones de filtros
def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, data)

def butter_highpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return lfilter(b, a, data)


file_path = r"C:\Users\ACER\Documents\Antecedentes\Señales\senal_emg.csv"
df = pd.read_csv(file_path)

time_column = df.columns[0]
signal_column = df.columns[1]

t = df[time_column].values
emg_signal = df[signal_column].values


dt = np.mean(np.diff(t))
sampling_rate = 1.0 / dt

# Aplicar filtros
low_cutoff = 20
high_cutoff = 450
filtered_signal = butter_highpass_filter(butter_lowpass_filter(emg_signal, high_cutoff, sampling_rate), low_cutoff, sampling_rate)

# Graficar señal original y filtrada
plt.figure(figsize=(12, 6))
plt.plot(t, emg_signal, label='Señal EMG original', color='navy')
plt.legend()

plt.figure(figsize=(12, 6))
plt.plot(t, filtered_signal, label="Señal Filtrada")
plt.xlabel("Tiempo (s)")
plt.ylabel("Amplitud")
plt.title("Señal EMG Filtrada")
plt.legend()
plt.show()

# Parámetros de ventana
window_size = int(0.682 * sampling_rate)  # 200 ms
step_size = window_size
num_windows = len(filtered_signal) // step_size

frecuencias_medias = []
potencias_espectrales = []

# Procesar cada ventana
for i in range(num_windows):
    start = i * step_size
    end = start + window_size
    if end > len(filtered_signal):
        break

    windowed_signal = filtered_signal[start:end] * np.hamming(window_size)
    freq_values = np.fft.fftfreq(window_size, d=dt)[:window_size // 2]
    fft_values = np.abs(fft(windowed_signal))[:window_size // 2]

    # PSD
    f_psd, Pxx = welch(windowed_signal, fs=sampling_rate, nperseg=window_size)

    # Métricas
    freq_mean = np.sum(f_psd * Pxx) / np.sum(Pxx)
    freq_median = f_psd[np.argmax(np.cumsum(Pxx) >= np.sum(Pxx) / 2)]
    freq_std = np.sqrt(np.sum(Pxx * (f_psd - freq_mean) ** 2) / np.sum(Pxx))

    frecuencias_medias.append(freq_mean)
    potencias_espectrales.append(Pxx)

    print(f"Ventana {i+1} - Frecuencia Media: {freq_mean:.2f} Hz, Mediana: {freq_median:.2f} Hz, Desviación estándar: {freq_std:.2f} Hz")

    # Graficar espectros
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(freq_values, fft_values)
    plt.xlabel("Frecuencia (Hz)")
    plt.ylabel("Magnitud")
    plt.title(f"Espectro de Frecuencia - Ventana {i+1}")

    plt.subplot(1, 2, 2)
    plt.semilogy(f_psd, Pxx)
    plt.xlabel("Frecuencia (Hz)")
    plt.ylabel("PSD")
    plt.title(f"Densidad Espectral de Potencia - Ventana {i+1}")
    plt.tight_layout()
    plt.show()


# PRUEBA DE HIPÓTESIS

frecuencias_medias = np.array(frecuencias_medias)

if len(frecuencias_medias) >= 10:
    grupo_inicial = frecuencias_medias[:5]
    grupo_final = frecuencias_medias[-5:]

    t_stat, p_value = ttest_ind(grupo_inicial, grupo_final)

    print("\n=== Prueba de Hipótesis (frecuencia media) ===")
    print(f"Frecuencia Media Inicial: {np.mean(grupo_inicial):.2f} Hz")
    print(f"Frecuencia Media Final: {np.mean(grupo_final):.2f} Hz")
    print(f"Estadístico t: {t_stat:.3f}")
    print(f"Valor p: {p_value:.4f}")

    if p_value < 0.05:
        print("Se rechaza la hipótesis nula: hay diferencia significativa entre el inicio y el final.")
    else:
        print("No se rechaza la hipótesis nula: no hay diferencia significativa entre el inicio y el final.")
