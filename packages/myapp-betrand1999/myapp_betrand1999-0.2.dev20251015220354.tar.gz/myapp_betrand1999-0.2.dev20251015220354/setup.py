from setuptools import setup, find_packages
import datetime

# Generate a version like 0.1.dev20250716010123
timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
version = f"0.2.dev{timestamp}"

setup(
    name='myapp-betrand1999',
    version=version,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'flask',
    ],
    entry_points={
        'console_scripts': [
            'myapp=myapp.app:main',
        ],
    },
)
