# setup.py

from setuptools import setup, find_packages
import os

# --- 1. Dependencies Load (Hardcoding to fix FileNotFoundError) ---
# हमने requirements.txt को पढ़ने के बजाय डिपेंडेंसी को सीधे यहां सूचीबद्ध किया है
# क्योंकि बिल्ड एनवायरनमेंट में requirements.txt नहीं मिल रहा था।
REQUIRED_PACKAGES = [
    'click',
    # ruamel.yaml को यहां जोड़ा गया है क्योंकि यह envcheck.py में उपयोग होता है
    'ruamel.yaml', 
]

# --- 2. README.md Load (UTF-8 Encoding Fix) ---
# UnicodeDecodeError को ठीक करने के लिए encoding='utf-8' का उपयोग करें।
try:
    with open('README.md', encoding='utf-8') as f:
        README_content = f.read()
except FileNotFoundError:
    # यदि README नहीं मिलती है तो इसे खाली स्ट्रिंग पर सेट करें
    README_content = ''

setup(
    name='envsanitycheck',
    version='1.0.0', 
    packages=find_packages(),
    
    # 3. Dependencies
    install_requires=REQUIRED_PACKAGES,
    
    # 4. Metadata
    author='Lokesh Kumar', # सुनिश्चित करें कि यह सही है
    description='A robust CLI tool for validating project environment variables (.env files) with type checking.',
    long_description=README_content,
    long_description_content_type='text/markdown',
    url='https://github.com/trmxvibs/EnvSanityCheck', # सुनिश्चित करें कि यह सही है
    license='MIT',
    
    # 5. Classifiers (PyPI के लिए ज़रूरी)
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7', # 3.6+ है, 3.7+ का उपयोग करना बेहतर है
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Utilities',
    ],
    
    # 6. Entry Point (कमांड 'envcheck' बनाने के लिए)
    entry_points={
        'console_scripts': [
            'envcheck = envsanitycheck.cli:envsanitycheck',
        ],
    },
)