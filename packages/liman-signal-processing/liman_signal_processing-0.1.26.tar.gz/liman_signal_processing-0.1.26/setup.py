from setuptools import setup, find_packages

# Чтение README.md для описания проекта
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="liman_signal_processing",
    version="0.1.26",
    author="Nikita Besednyi",
    author_email="besednyi_n@liman-tech.ru",
    description="Библиотека для обработки сырого сигнала в системах вибродиагностики и токовой диагностики",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.22.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "aiobotocore~=2.19.0",
        "pyarrow~=19.0.0",
        "pandas~=2.2.3",
        "clickhouse-driver~=0.2.9",
        "pydantic~=2.10.3"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",  # Для тестирования
            "black>=21.0",  # Для форматирования кода
        ],
    },
    include_package_data=True,  # Включает не-Python файлы (например, данные)
)