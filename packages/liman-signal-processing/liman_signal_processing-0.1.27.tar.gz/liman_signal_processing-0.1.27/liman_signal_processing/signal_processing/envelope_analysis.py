import numpy as np
from scipy.signal import hilbert
from .frequency_analysis import compute_amplitude_spectrum
from .preprocessing import filter_signal, apply_window

def compute_envelope_spectrum(signal, sampling_rate, lowcut, highcut,
                             window_type=None, frequency_resolution=None):
    """
    Вычисляет спектр огибающей сигнала с возможностью управления частотным разрешением.

    :param signal: Входной сигнал.
    :param sampling_rate: Частота дискретизации (Гц).
    :param lowcut: Нижняя граница полосы фильтра (Гц).
    :param highcut: Верхняя граница полосы фильтра (Гц).
    :param window_type: Тип окна (None, 'hann', 'hamming', 'blackman').
    :param frequency_resolution: Желаемое частотное разрешение (Гц). Если None, используется длина сигнала.
    :return: Кортеж (frequencies, envelope_spectrum), где:
             - frequencies: Массив частот (Гц).
             - envelope_spectrum: Спектр огибающей.
    """
    # Применяем полосовой фильтр
    filtered_signal = signal
    if lowcut is not None and highcut is not None:
        filter_type = 'bandpass'
        if lowcut == 0:
            filter_type = 'lowpass'
        filtered_signal = filter_signal(signal, (lowcut, highcut), sampling_rate, filter_type)

    # Накладываем окно (если указано)
    if window_type is not None:
        filtered_signal = apply_window(filtered_signal, window_type)

    # Вычисляем огибающую с помощью преобразования Гильберта
    analytic_signal = hilbert(filtered_signal)
    envelope = np.abs(analytic_signal)

    # Вычисляем спектр огибающей с заданным разрешением
    frequencies, spectrum, phase = compute_amplitude_spectrum(
        envelope,
        sampling_rate,
        window_type=window_type,
        frequency_resolution=frequency_resolution
    )

    return frequencies, spectrum, phase