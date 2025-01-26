from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nexus-scanner",
    version="1.0.0",
    author="Nexus Security Team",
    author_email="team@nexus-scanner.io",
    description="A powerful security scanning platform for modern infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nexus/nexus-scanner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
        "beautifulsoup4>=4.11.0",
        "pyyaml>=6.0.0",
        "rich>=12.0.0",
        "click>=8.1.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.2.0',
            'pytest-asyncio>=0.20.0',
            'black>=22.12.0',
            'mypy>=0.991',
            'flake8>=6.0.0',
        ],
        'docs': [
            'sphinx>=5.3.0',
            'mkdocs>=1.4.0',
            'mkdocs-material>=8.5.0',
        ],
        'enterprise': [
            'prometheus-client>=0.15.0',
            'fastapi>=0.88.0',
            'uvicorn>=0.20.0',
            'redis>=4.4.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'nexus=nexus.cli:main',
            'nexus-admin=nexus.admin:main',
        ],
    },
    package_data={
        'nexus': [
            'config/*.yaml',
            'templates/*.html',
            'static/css/*.css',
            'static/js/*.js',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    project_urls={
        'Documentation': 'https://docs.nexus-scanner.io',
        'Source': 'https://github.com/nexus/nexus-scanner',
        'Tracker': 'https://github.com/nexus/nexus-scanner/issues',
    },
    keywords=[
        'security',
        'scanner',
        'vulnerability',
        'pentest',
        'cybersecurity',
        'infosec',
        'devsecops',
    ],
)
