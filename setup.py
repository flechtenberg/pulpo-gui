from setuptools import setup, find_packages

setup(
    name="pulpo-gui",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pulpo-dev[bw2]",
        "streamlit",
    ],
    entry_points={
        'console_scripts': [
            'pulpo-gui = pulpo_gui.app:main'
        ]
    }
)
