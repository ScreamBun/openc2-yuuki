from pathlib import Path
from pkg_resources import parse_requirements
from setuptools import setup


def get_requirements():
    with Path('requirements.txt').open() as req:
        return [str(req) for req in parse_requirements(req)]


setup(
    name='Yuuki',
    package_data={
        'Yuuki': ['./oc2_arch/*'],
    },
    install_requires=get_requirements()
)
