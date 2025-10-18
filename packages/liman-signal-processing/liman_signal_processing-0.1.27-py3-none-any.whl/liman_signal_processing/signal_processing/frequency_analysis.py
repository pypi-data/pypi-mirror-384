import math
import numpy as np
from scipy.fftpack import fft

from .preprocessing import filter_signal, apply_window


def _create_overlapping_segments(signal, segment_length, overlap_ratio=0.5):
    """
    Разбивает сигнал на перекрывающиеся сегменты для усреднения спектров.
    Корректно обрабатывает случаи, когда сигнал не позволяет создать сегменты с заданным перекрытием.
    
    :param signal: Входной сигнал.
    :param segment_length: Длина каждого сегмента в отсчетах.
    :param overlap_ratio: Коэффициент перекрытия (0.0 - без перекрытия, 0.5 - 50% перекрытия).
    :return: Список сегментов сигнала.
    """
    if len(signal) <= segment_length:
        return [signal]
    
    segments = []
    
    # Вычисляем идеальный шаг для заданного перекрытия
    ideal_step = int(segment_length * (1 - overlap_ratio))
    
    # Проверяем, можем ли мы создать хотя бы два сегмента с идеальным перекрытием
    if len(signal) < segment_length + ideal_step:
        # Если нет, создаем два сегмента с минимальным перекрытием
        # Первый сегмент: начало сигнала
        segments.append(signal[:segment_length])
        
        # Второй сегмент: конец сигнала (с перекрытием, если возможно)
        remaining_length = len(signal) - segment_length
        if remaining_length > 0:
            # Вычисляем минимальное перекрытие для второго сегмента
            min_overlap = max(0, segment_length - remaining_length)
            start_second = segment_length - min_overlap
            segments.append(signal[start_second:])
    else:
        # Обычный случай: создаем сегменты с заданным перекрытием
        for start in range(0, len(signal) - segment_length + 1, ideal_step):
            end = start + segment_length
            segments.append(signal[start:end])
            
            # Проверяем, не выходим ли мы за границы сигнала
            if end >= len(signal):
                break
    
    return segments


def _compute_single_segment_spectrum(segment, sampling_rate, window_type=None, n_fft=None):
    """
    Вычисляет спектр одного сегмента сигнала.
    
    :param segment: Сегмент сигнала.
    :param sampling_rate: Частота дискретизации.
    :param window_type: Тип окна (None, 'hann', 'hamming', 'blackman').
    :param n_fft: Длина БПФ.
    :return: Кортеж (frequencies, amplitude_spectrum, phase_spectrum).
    """
    # Накладываем окно (если указано) и вычисляем поправочный коэффициент
    window_correction = 1.0
    if window_type is not None:
        if window_type == 'hann':
            window = np.hanning(len(segment))
        elif window_type == 'hamming':
            window = np.hamming(len(segment))
        elif window_type == 'blackman':
            window = np.blackman(len(segment))
        else:
            raise ValueError("Неизвестный тип окна")
        
        window_correction = np.mean(window)
        segment = segment * window
    
    # Определяем длину БПФ
    n_original = len(segment)
    if n_fft is None:
        n_fft = n_original
    elif n_fft > n_original:
        segment = np.pad(segment, (0, n_fft - n_original), 'constant')
    
    # Вычисляем БПФ
    fft_result = fft(segment, n=n_fft)
    
    # Берем только первую половину спектра (односторонний спектр)
    fft_result = fft_result[:n_fft // 2]
    
    # Вычисляем амплитудный спектр с поправкой на окно
    amplitude_spectrum = np.abs(fft_result) / (n_original * window_correction)
    if n_fft > 1:  # Коррекция амплитуды (кроме DC и Найквиста)
        amplitude_spectrum[1:-1] *= 2
    
    # Вычисляем фазовый спектр (в радианах)
    phase_spectrum = 180 / math.pi * np.angle(fft_result)
    
    # Частотная ось
    frequencies = np.fft.fftfreq(n_fft, 1 / sampling_rate)[:n_fft // 2]
    
    return frequencies, amplitude_spectrum, phase_spectrum


def _average_spectra(spectra_list):
    """
    Усредняет список спектров.
    
    :param spectra_list: Список кортежей (frequencies, amplitude_spectrum, phase_spectrum).
    :return: Кортеж (frequencies, averaged_amplitude_spectrum, averaged_phase_spectrum).
    """
    if not spectra_list:
        raise ValueError("Список спектров не может быть пустым")
    
    if len(spectra_list) == 1:
        return spectra_list[0]
    
    # Извлекаем частоты (они должны быть одинаковыми для всех спектров)
    frequencies = spectra_list[0][0]
    
    # Усредняем амплитудные спектры
    amplitude_spectra = [spec[1] for spec in spectra_list]
    averaged_amplitude = np.mean(amplitude_spectra, axis=0)
    
    # Усредняем фазовые спектры (используем комплексное усреднение для корректной обработки фаз)
    phase_spectra = [spec[2] for spec in spectra_list]
    # Конвертируем фазы в комплексные числа для усреднения
    complex_phases = [np.exp(1j * np.deg2rad(phase)) for phase in phase_spectra]
    averaged_complex_phase = np.mean(complex_phases, axis=0)
    averaged_phase = np.rad2deg(np.angle(averaged_complex_phase))
    
    return frequencies, averaged_amplitude, averaged_phase


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
                                     window_type=None, frequency_resolution=None,
                                     enable_averaging=True, overlap_ratio=0.5, max_segments=None):
    """
    Вычисляет амплитудный и фазовый спектры сигнала с возможностью фильтрации и наложения окна.
    Поддерживает усреднение спектров для уменьшения шумов при избытке данных.

    :param signal: Входной сигнал.
    :param sampling_rate: Частота дискретизации.
    :param lowcut: Нижняя граница полосы фильтра (Гц). Если None, фильтр не применяется.
    :param highcut: Верхняя граница полосы фильтра (Гц). Если None, фильтр не применяется.
    :param window_type: Тип окна (None, 'hann', 'hamming', 'blackman').
    :param frequency_resolution: Желаемое частотное разрешение (Гц). Если None, используется длина сигнала.
    :param enable_averaging: Включить усреднение спектров при избытке данных.
    :param overlap_ratio: Коэффициент перекрытия сегментов для усреднения (0.0-0.9).
    :param max_segments: Максимальное количество сегментов для усреднения. Если None, ограничений нет.
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

    # Определяем длину БПФ
    n_original = len(signal)
    if frequency_resolution is not None:
        n_fft = int(sampling_rate / frequency_resolution)
    else:
        n_fft = n_original

    # Проверяем, нужно ли использовать усреднение
    if enable_averaging and n_fft < n_original:
        # Вычисляем оптимальную длину сегмента для усреднения
        segment_length = n_fft
        
        # Создаем перекрывающиеся сегменты
        segments = _create_overlapping_segments(signal, segment_length, overlap_ratio)
        
        # Ограничиваем количество сегментов если указано
        if max_segments is not None and len(segments) > max_segments:
            # Выбираем сегменты равномерно по всему сигналу
            step = len(segments) // max_segments
            segments = segments[::step][:max_segments]
        
        # Вычисляем спектры для каждого сегмента
        spectra_list = []
        for segment in segments:
            freq, amp, phase = _compute_single_segment_spectrum(
                segment, sampling_rate, window_type, n_fft
            )
            spectra_list.append((freq, amp, phase))
        
        # Усредняем спектры
        frequencies, amplitude_spectrum, phase_spectrum = _average_spectra(spectra_list)
        
    else:
        # Стандартная обработка без усреднения
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

        # Если нужно больше точек, чем есть в сигнале - дополняем нулями
        if n_fft > n_original:
            signal = np.pad(signal, (0, n_fft - n_original), 'constant')
        else:
            n_fft = n_original  # Нельзя уменьшить разрешение без потери данных

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