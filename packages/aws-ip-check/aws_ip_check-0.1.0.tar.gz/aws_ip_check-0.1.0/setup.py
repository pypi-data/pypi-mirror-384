from setuptools import setup, find_packages

setup(
    name='aws-ip-check',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'aws-ip-check = aws_ip_check.cli:main',
        ],
    },
    python_requires='>=3.7',
    description='Check if IPs belong to AWS ranges',
)
