from setuptools import setup

setup(
    name="cookk",
    version="1.3.0",
    author="Cook Utility", 
    description="A cooking utility tool",
    py_modules=["cook"],
    install_requires=[
        "requests>=2.25.1",
    ],
    entry_points={
        'console_scripts': [
            'cook=cook:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
