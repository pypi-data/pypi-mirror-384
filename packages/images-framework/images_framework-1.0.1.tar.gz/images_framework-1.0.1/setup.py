from setuptools import setup, find_packages

setup(
    name='images_framework',
    version='1.0.1',
    package_dir={'images_framework': 'images_framework'},
    packages=find_packages(include=['images_framework.src', 'images_framework.src.*', 'images_framework.categories', 'images_framework.categories.*']),
    install_requires=[
        'numpy',
        'scipy',
        'opencv-python',
        'opencv-contrib-python',
        'rasterio',
        'pillow',
        'pascal-voc-writer'
    ],
    extras_require={
        'gdal': ['gdal']
    },
    author='Roberto Valle',
    author_email='roberto.valle@upm.es',
    description='A modular computer vision framework developed by PCR-UPM for image processing tasks.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/pcr-upm/images_framework',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
