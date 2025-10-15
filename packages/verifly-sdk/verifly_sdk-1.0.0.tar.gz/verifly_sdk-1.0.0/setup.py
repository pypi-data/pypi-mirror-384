"""
Setup configuration for Verifly Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='verifly-sdk',
    version='1.0.0',
    description='Official Python SDK for Verifly - Inbound 2FA Verification System with HMAC-SHA256 Authentication',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='SOCIFLY SOFTWARE LTD.',
    author_email='info@verifly.net',
    url='https://www.verifly.net',
    project_urls={
        'Documentation': 'https://www.verifly.net/docs',
        'Source': 'https://github.com/tlgsn/verifly-python-sdk',
        'Bug Reports': 'https://github.com/tlgsn/verifly-python-sdk/issues',
    },
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'requests>=2.25.0',
    ],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Security',
        'Topic :: Communications',
    ],
    keywords='verifly 2fa verification sms whatsapp email otp authentication',
    license='MIT',
    zip_safe=False,
)
