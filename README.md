# Señales electromiográficas EMG
## Descripción

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
![image](https://github.com/user-attachments/assets/f9c9e537-395a-4790-bb27-ca431dcdc490)
