import math
import numpy as np
from scipy.fftpack import fft

from .preprocessing import filter_signal, apply_window


def third_octave_bands(sampling_rate):
    """
    Возвращает центральные частоты и границы третьоктавных полос, ограниченные частотой Найквиста.

    :param sampling_rate: Частота дискретизации.
    :return: Список кортежей (нижняя граница, центральная частота, верхняя граница).
    """
    # Стандартные центральные частоты (по ГОСТ или ISO)
    centers = [16, 20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200,
               250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000,
               2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000]

    # Частота Найквиста
    nyquist = 0.5 * sampling_rate

    # Границы полос (нижняя и верхняя частота)
    bands = []
    for fc in centers:
        fl = fc / (2 ** (1 / 6))  # Нижняя граница
        fu = fc * (2 ** (1 / 6))  # Верхняя граница

        # Проверяем, что верхняя граница не превышает частоту Найквиста
        if fu <= nyquist:
            bands.append((fl, fc, fu))

    return bands

def compute_amplitude_spectrum(signal, sampling_rate, lowcut=None, highcut=None,
                                     window_type=None, frequency_resolution=None):
    """
    Вычисляет амплитудный и фазовый спектры сигнала с возможностью фильтрации и наложения окна.

    :param signal: Входной сигнал.
    :param sampling_rate: Частота дискретизации.
    :param lowcut: Нижняя граница полосы фильтра (Гц). Если None, фильтр не применяется.
    :param highcut: Верхняя граница полосы фильтра (Гц). Если None, фильтр не применяется.
    :param window_type: Тип окна (None, 'hann', 'hamming', 'blackman').
    :param frequency_resolution: Желаемое частотное разрешение (Гц). Если None, используется длина сигнала.
    :return: Кортеж (frequencies, amplitude_spectrum, phase_spectrum), где:
             - frequencies: Массив частот (Гц).
             - amplitude_spectrum: Амплитудный спектр сигнала.
             - phase_spectrum: Фазовый спектр сигнала (в радианах).
    """
    # Применяем полосовой фильтр (если указаны границы)
    if lowcut is not None and highcut is not None:
        filter_type = 'bandpass'
        if lowcut == 0:
            filter_type = 'lowpass'
            signal = filter_signal(signal, highcut, sampling_rate, filter_type)
        else:
            signal = filter_signal(signal, (lowcut, highcut), sampling_rate, filter_type)

    # Накладываем окно (если указано) и вычисляем поправочный коэффициент
    window_correction = 1.0
    if window_type is not None:
        # Вычисляем поправочный коэффициент для компенсации эффекта окна
        if window_type == 'hann':
            window = np.hanning(len(signal))
        elif window_type == 'hamming':
            window = np.hamming(len(signal))
        elif window_type == 'blackman':
            window = np.blackman(len(signal))
        else:
            raise ValueError("Неизвестный тип окна")
        
        # Поправочный коэффициент - среднее значение окна
        window_correction = np.mean(window)
        signal = signal * window

    # Определяем длину БПФ
    n_original = len(signal)
    if frequency_resolution is not None:
        # Вычисляем требуемое количество точек для заданного разрешения
        n_fft = int(sampling_rate / frequency_resolution)
        # Если нужно больше точек, чем есть в сигнале - дополняем нулями
        if n_fft > n_original:
            signal = np.pad(signal, (0, n_fft - n_original), 'constant')
        else:
            n_fft = n_original  # Нельзя уменьшить разрешение без потери данных
    else:
        n_fft = n_original  # Используем исходную длину

    # Вычисляем БПФ
    fft_result = fft(signal, n=n_fft)

    # Берем только первую половину спектра (односторонний спектр)
    fft_result = fft_result[:n_fft // 2]

    # Вычисляем амплитудный спектр с поправкой на окно
    amplitude_spectrum = np.abs(fft_result) / (n_original * window_correction)  # Нормализация с поправкой на окно
    if n_fft > 1:  # Коррекция амплитуды (кроме DC и Найквиста)
        amplitude_spectrum[1:-1] *= 2

    # Вычисляем фазовый спектр (в радианах)
    phase_spectrum = 180 / math.pi * np.angle(fft_result)

    # Частотная ось
    frequencies = np.fft.fftfreq(n_fft, 1 / sampling_rate)[:n_fft // 2]

    return frequencies, amplitude_spectrum, phase_spectrum

def compute_phase_spectrum(signal, sampling_rate):
    """
    Вычисляет фазовый спектр сигнала с использованием быстрого преобразования Фурье (FFT).

    :param signal: Входной сигнал (numpy array).
    :param sampling_rate: Частота дискретизации сигнала (Гц).
    :return: Кортеж (frequencies, phases), где:
             - frequencies: Массив частот (Гц).
             - phases: Фазовый спектр сигнала (в радианах).
    """
    n = len(signal)  # Длина сигнала
    k = np.arange(n)
    T = n / sampling_rate
    frequencies = k / T  # Массив частот

    # Вычисляем FFT и фазы
    spectrum = fft(signal)
    phases = np.angle(spectrum[:n // 2])  # Берем только первую половину спектра

    # Соответствующие частоты для первой половины спектра
    frequencies = frequencies[:n // 2]

    return frequencies, phases

def third_octave_spectrum(signal, sampling_rate):
    """
    Вычисляет третьоктавный спектр сигнала.

    :param signal: Входной сигнал.
    :param sampling_rate: Частота дискретизации.
    :return: Кортеж (центры, уровни), где:
             - центры: Центральные частоты.
             - уровни: Уровни сигнала в каждой полосе (в dB).
    """
    bands = third_octave_bands(sampling_rate)
    centers = [band[1] for band in bands]
    levels = []

    for fl, fc, fu in bands:
        # Применяем полосовой фильтр
        filtered_signal = filter_signal(signal, (fl, fu), sampling_rate, 'bandpass')

        # Вычисляем энергию сигнала в полосе
        energy = np.sum(filtered_signal ** 2) / len(filtered_signal)

        # Переводим энергию в dB
        level = 10 * np.log10(energy + 1e-12)  # Добавляем малую величину, чтобы избежать log(0)
        levels.append(level)

    return centers, levels