from setuptools import setup, find_packages
from pathlib import Path

# Leer el contenido del README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name='nestling_growth_app',          # en PyPI se muestra como nestling-growth-app
    version='0.1.10',                     # debe coincidir con tu release v0.1.9
    packages=find_packages(include=['nestling_app', 'nestling_app.*']),
    include_package_data=True,
    install_requires=[
        'dash',
        'pandas',
        'numpy',
        'matplotlib',
        'plotly',
        'scipy',
        'fastapi',
        'uvicorn',
        'kaleido',
        'gunicorn'
    ],
    entry_points={
        'console_scripts': [
            'nestling-app = nestling_app.api.app:main'
        ]
    },

    # --- Metadatos ---
    author='Jorge Lizarazo, Juan Camilo Guerra & Gustavo A Londoño',
    author_email='jorge.lizarazo.b@gmail.com',
    description='An interactive Dash app to analyze nestling growth using biological models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jorgelizarazo94/NestlingGrowthApp',
    project_urls={
        'Homepage': 'https://github.com/jorgelizarazo94/NestlingGrowthApp',
        'PyPI': 'https://pypi.org/project/nestling-growth-app/',
        'Issue Tracker': 'https://github.com/jorgelizarazo94/NestlingGrowthApp/issues',
        'DOI': 'https://doi.org/10.5281/zenodo.17360999',
    },
    license='MIT',
    license_files=('LICENSE',),

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Dash',
    ],
    python_requires='>=3.7',
    keywords=['ornithology', 'growth models', 'dash', 'ecology', 'biology'],
)