from setuptools import setup, find_packages

setup(
    name="SeleniumTwo",
    version="0.3.2",
    author="Guilherme Neri",
    author_email="gui.neriaz@gmail.com",
    description="Neri library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/NeriAzv/Neri-Library",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            *[f"{cmd}=SeleniumTwo.cli:main" for cmd in [
                "SeleniumTwo",
                "ST",
                "st",
                "selenium2"
            ]],
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        'setuptools',
        'pyperclip',
        'pyinstaller',
        'selenium',
    ],
    extras_require={
        "pynput": [
            'pynput',
        ],
        "screeninfo": [
            'screeninfo',
        ],
        "pywinauto": [
            'pywinauto',
        ],
        "capmonstercloudclient":[
            'capmonstercloudclient',
        ],
        "twocaptcha":[
            "2captcha-python",
        ],
        "full": [
            'undetected-chromedriver',
            'webdriver-manager',
            'opencv-python',
            'pygetwindow',
            'pyinstaller',
            'screeninfo',
            'pyscreeze',
            'pyautogui',
            'selenium',
            'requests',
            'pymupdf',
            'Pillow',
            'psutil',
            'pynput',
        ],
    },
)
