#!/usr/bin/env python3
"""
Setup script for Secure HTTP Server.
"""

import os
import sys
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


def read_file(filename):
    """Read file contents."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def get_version():
    """Extract version from __init__.py."""
    init_file = Path("secure_server/__init__.py")
    with open(init_file, 'r') as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"')
    return "1.0.0"


class PostInstallCommand(install):
    """Custom post-installation commands."""
    
    def run(self):
        install.run(self)
        print("\n" + "="*60)
        print("Secure HTTP Server has been installed successfully!")
        print("="*60)
        print("\nTo start the server:")
        print("  secure-http-server")
        print("\nTo manage users:")
        print("  secure-http-server --manage-users")
        print("\nFor more options:")
        print("  secure-http-server --help")
        print("="*60 + "\n")


class PostDevelopCommand(develop):
    """Custom post-development installation commands."""
    
    def run(self):
        develop.run(self)
        print("\nDevelopment installation complete!")


install_requires = [
]

extras_require = {
}

setup(
    name='secure-http-server',
    version=get_version(),
    author='Mohamed Elmoncef HAMDI',
    author_email='mohamedelmoncef.hamdi@gmail.com',
    description='A secure HTTP server with authentication and file management',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/moncef007/secure-http-server',
    project_urls={
        'Bug Reports': 'https://github.com/moncef007/secure-http-server/issues',
        'Source': 'https://github.com/moncef007/secure-http-server',
        'Documentation': 'https://secure-http-server.readthedocs.io',
    },
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Security',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Environment :: Console',
    ],
    keywords='http server authentication security file-sharing',
    packages=find_packages(exclude=['tests', 'tests.*', 'docs', 'docs.*']),
    python_requires='>=3.7',
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'secure-http-server=secure_server.__init__:main',
            'shs=secure_server.__init__:main',
        ],
    },
    include_package_data=True,
    package_data={
        'secure_server': ['py.typed'],
    },
    zip_safe=False,
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
)