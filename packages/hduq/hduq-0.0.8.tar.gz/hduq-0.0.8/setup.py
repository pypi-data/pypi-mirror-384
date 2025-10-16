from setuptools import setup, find_packages

setup(
    name='hduq',
    version='0.0.8',
    packages=find_packages(),
    include_package_data=True,
    package_data={'hduq.assets': ['*']},
    # entry_points={
    #     'console_scripts': [
    #         'hduq=hduq.cli:main',
    #     ],
    # },
    install_requires=[
        'numpy',
        'pandas',
        'scipy',
        'Pillow',
        'opencv-python',
        'dask',
        'psutil'
    ],
    license='GPLv3',
    license_files='LICENSE',
    python_requires='>=3.9',
    description='HDUQ Python utils',
    author='Chao-Ning Hu',
)
