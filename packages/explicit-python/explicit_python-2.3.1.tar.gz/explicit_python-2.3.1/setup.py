from pathlib import Path

from setuptools import find_namespace_packages
from setuptools import setup


def _read(file_path):
    with open(file_path, 'r') as infile:
        return infile.read()


setup(
    name='explicit-python',
    license='MIT',
    author='BARS Group',
    description='Набор компонентов для построения многослойной архитектуры',
    author_email='education_dev@bars-open.ru',
    package_dir={'': 'src'},
    packages=find_namespace_packages('src', exclude=('testapp', 'testapp.*',)),
    install_requires=(
        'pydantic<2.0',  # См. explicit.domain.model._VALIDATORS
        'more_itertools'
    ),
    long_description=_read('README.md'),
    long_description_content_type='text/markdown',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Development Status :: 5 - Production/Stable',
    ],
    dependency_links=(
        'https://pypi.bars-open.ru/simple/m3-builder',
    ),
    setup_requires=(
        'm3-builder>=1.2,<2',
    ),
    set_build_info=Path(__file__).parent,
)
