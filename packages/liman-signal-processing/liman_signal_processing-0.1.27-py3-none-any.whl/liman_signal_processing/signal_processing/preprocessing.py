import numpy as np
from scipy import signal


def filter_signal(data, cutoff_freq, sampling_rate, filter_type='lowpass'):
    """
    Фильтрация сигнала с автоматической обработкой частот >= частоты Найквиста.

    Функция автоматически ограничивает частоты среза частотой Найквиста (0.5 * sampling_rate)
    для предотвращения ошибок фильтрации. Если частота среза превышает частоту Найквиста,
    она автоматически ограничивается до 0.99 * частота_Найквиста.

    :param data: Входной сигнал (numpy array).
    :param cutoff_freq: Частота среза (одна частота для lowpass/highpass, кортеж (lowcut, highcut) для bandpass).
    :param sampling_rate: Частота дискретизации.
    :param filter_type: Тип фильтра ('lowpass', 'highpass', 'bandpass').
    :return: Отфильтрованный сигнал.
    :raises ValueError: Если частота дискретизации <= 0 или сигнал пустой.
    """
    nyquist_freq = 0.5 * sampling_rate
    
    # Валидация входных параметров
    if sampling_rate <= 0:
        return data

    if len(data) == 0:
        return data

    if filter_type == 'bandpass':
        # Для полосового фильтра cutoff_freq должен быть кортежем (lowcut, highcut)
        lowcut, highcut = cutoff_freq
        
        # Ограничиваем частоты частотой Найквиста
        lowcut = min(lowcut, nyquist_freq * 0.99)  # 0.99 для избежания проблем с границей
        highcut = min(highcut, nyquist_freq * 0.99)
        
        # Проверяем, что lowcut < highcut после ограничения
        if lowcut >= highcut:
            # Если полоса стала слишком узкой, используем lowpass фильтр
            filter_type = 'lowpass'
            cutoff_freq = highcut
            normal_cutoff = cutoff_freq / nyquist_freq
        else:
            normal_cutoff = [lowcut / nyquist_freq, highcut / nyquist_freq]
    else:
        # Для lowpass/highpass cutoff_freq — это одна частота
        # Ограничиваем частоту среза частотой Найквиста
        cutoff_freq = min(cutoff_freq, nyquist_freq * 0.99)
        normal_cutoff = cutoff_freq / nyquist_freq

    # Создаем фильтр
    b, a = signal.butter(4, normal_cutoff, btype=filter_type)
    filtered_data = signal.filtfilt(b, a, data)
    return filtered_data

def apply_window(data, window_type='hann'):
    """
    Накладывает оконную функцию на сигнал.

    :param data: Входной сигнал.
    :param window_type: Тип окна ('hann', 'hamming', 'blackman').
    :return: Сигнал с наложенным окном.
    """
    if window_type == 'hann':
        window = np.hanning(len(data))
    elif window_type == 'hamming':
        window = np.hamming(len(data))
    elif window_type == 'blackman':
        window = np.blackman(len(data))
    else:
        raise ValueError("Неизвестный тип окна")

    return data * window