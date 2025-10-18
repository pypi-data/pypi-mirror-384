import numpy as np
from scipy.fft import fft, ifft, fftfreq


def acceleration_to_velocity_time(a, t_ns, remove_dc=True):
    """
    Переводит виброускорение (м/с²) в виброскорость (мм/с) через FFT.

    Параметры:
    a : array-like
        Массив значений виброускорения в м/с².
    t_ns : array-like
        Массив времени в наносекундах (нс).
    remove_dc : bool, optional
        Удалять ли постоянную составляющую (по умолчанию True).

    Возвращает:
    v_mm_s : array-like
        Виброскорость в мм/с.
    """
    t_s = t_ns * 1e-9  # Наносекунды → секунды
    dt_s = t_s[1] - t_s[0]  # Шаг дискретизации в секундах
    n = len(a)

    if remove_dc:
        a = a - np.mean(a)

    A = fft(a)
    freqs = fftfreq(n, dt_s)

    V = np.zeros_like(A, dtype=complex)
    mask = np.abs(freqs) > 1e-6  # Игнорируем f=0
    V[mask] = A[mask] / (2j * np.pi * freqs[mask])

    v = ifft(V).real
    v_mm_s = v * 1000  # м/с → мм/с
    return v_mm_s


def velocity_to_displacement_time(v, t_ns, remove_dc=True):
    """
    Переводит виброскорость (мм/с) в виброперемещение (мкм) через FFT.

    Параметры:
    v : array-like
        Массив значений виброскорости в мм/с.
    t_ns : array-like
        Массив времени в наносекундах (нс).
    remove_dc : bool, optional
        Удалять ли постоянную составляющую (по умолчанию True).

    Возвращает:
    x_um : array-like
        Виброперемещение в микрометрах (мкм).
    """
    t_s = t_ns * 1e-9  # Наносекунды → секунды
    dt_s = t_s[1] - t_s[0]  # Шаг дискретизации в секундах
    n = len(v)

    if remove_dc:
        v = v - np.mean(v)

    # Переводим мм/с → м/с для корректного интегрирования
    v_m_s = v / 1000

    V = fft(v_m_s)
    freqs = fftfreq(n, dt_s)

    X = np.zeros_like(V, dtype=complex)
    mask = np.abs(freqs) > 1e-6
    X[mask] = V[mask] / (2j * np.pi * freqs[mask])

    x = ifft(X).real
    x_um = x * 1e6  # м → мкм
    return x_um


def acceleration_to_displacement_time(a, t_ns, remove_dc=True):
    """
    Переводит виброускорение (м/с²) в виброперемещение (мкм) через FFT.

    Параметры:
    a : array-like
        Массив значений виброускорения в м/с².
    t_ns : array-like
        Массив времени в наносекундах (нс).
    remove_dc : bool, optional
        Удалять ли постоянную составляющую (по умолчанию True).

    Возвращает:
    x_um : array-like
        Виброперемещение в микрометрах (мкм).
    """
    t_s = t_ns * 1e-9  # Наносекунды → секунды
    dt_s = t_s[1] - t_s[0]  # Шаг дискретизации в секундах
    n = len(a)

    if remove_dc:
        a = a - np.mean(a)

    A = fft(a)
    freqs = fftfreq(n, dt_s)

    X = np.zeros_like(A, dtype=complex)
    mask = np.abs(freqs) > 1e-6
    X[mask] = A[mask] / (-4 * np.pi ** 2 * freqs[mask] ** 2)

    x = ifft(X).real
    x_um = x * 1e6  # м → мкм
    return x_um


def acceleration_to_velocity_spectrum(A, frequencies):
    """
    Переводит спектр виброускорения в спектр виброскорости.

    Параметры:
    A : array-like
        Массив значений спектра виброускорения.
    frequencies : array-like
        Массив частот, соответствующих значениям спектра.

    Возвращает:
    V : array-like
        Массив значений спектра виброскорости.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        V = A / (2 * np.pi * frequencies)
    V[frequencies == 0] = 0  # Убираем нулевую частоту
    return V


def velocity_to_displacement_spectrum(V, frequencies):
    """
    Переводит спектр виброскорости в спектр виброперемещения.

    Параметры:
    V : array-like
        Массив значений спектра виброскорости.
    frequencies : array-like
        Массив частот, соответствующих значениям спектра.

    Возвращает:
    X : array-like
        Массив значений спектра виброперемещения.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        X = V / (2 * np.pi * frequencies)
    X[frequencies == 0] = 0  # Убираем нулевую частоту
    return X


def acceleration_to_displacement_spectrum(A, frequencies):
    """
    Переводит спектр виброускорения в спектр виброперемещения.

    Параметры:
    A : array-like
        Массив значений спектра виброускорения.
    frequencies : array-like
        Массив частот, соответствующих значениям спектра.

    Возвращает:
    X : array-like
        Массив значений спектра виброперемещения.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        X = A / (2 * np.pi * frequencies) ** 2
    X[frequencies == 0] = 0  # Убираем нулевую частоту
    return X


def acceleration_to_decibels(acceleration_spectrum, reference=1e-6):
    """
    Преобразует спектр виброускорения в спектр в децибелах.

    :param acceleration_spectrum: Массив с данными спектра виброускорения (м/с^2).
    :param reference: Опорное значение для расчета децибел (по умолчанию 1e-6 м/с^2).
    :return: Спектр виброускорения в децибелах.
    """
    # Преобразуем ускорение в децибелы
    decibel_spectrum = 20 * np.log10(np.abs(acceleration_spectrum) / reference)

    return decibel_spectrum