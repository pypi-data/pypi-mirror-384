from setuptools import setup, find_packages
from pathlib import Path

# Read README
long_description = (Path(__file__).parent / "README.md").read_text(encoding='utf-8')

setup(
    name="knf-predictor",
    version="2.0.0",
    author="Prasanna P. Kulkarni",
    author_email="prasannakulkarni163@gmail.com",
    description="🧠 AI-powered KNF prediction for supramolecular stability",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/prasanna-kulkarni/knf-predictor",
    project_urls={
        "Bug Tracker": "https://github.com/prasanna-kulkarni/knf-predictor/issues",
        "Documentation": "https://knf-predictor.readthedocs.io",
        "Paper": "https://doi.org/10.1021/acs.jcim.xxxxx",
    },
    packages=find_packages(),
    include_package_data=True,  # CRITICAL for bundling model
    package_data={
        'knf_predictor': ['data/*.pth'],  # Include model file
    },
    install_requires=[
        "torch>=2.0.0",
        "torch-geometric>=2.3.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "tqdm>=4.65.0",
    ],
    entry_points={
        'console_scripts': [
            'knf-predict=knf_predictor.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.8',
    keywords='chemistry machine-learning deep-eutectic-solvents molecular-modeling',
)
