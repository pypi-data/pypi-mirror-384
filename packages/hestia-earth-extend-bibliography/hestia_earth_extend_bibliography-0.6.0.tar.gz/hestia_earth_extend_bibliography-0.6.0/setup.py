from setuptools import find_namespace_packages, setup

from hestia_earth.extend_bibliography.version import VERSION


with open('README.md', 'r') as fh:
    long_description = fh.read()


with open('requirements.txt', 'r') as fh:
    REQUIRES = list(filter(lambda x: not x.startswith('git'), fh.read().splitlines()))


setup(
    name='hestia_earth_extend_bibliography',
    version=VERSION,
    description='Hestia library to extend Bibliography Nodes with different APIs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Guillaume Royer',
    author_email='guillaumeroyer.mail@gmail.com',
    license='MIT',
    url='https://gitlab.com/hestia-earth/hestia-data-validation',
    keywords=['hestia', 'mendeley'],
    packages=find_namespace_packages(include=['hestia_earth.*']),
    python_requires='>=3.12',
    classifiers=[],
    install_requires=REQUIRES,
    dependency_links=[
        'git+git://github.com/hestia-earth/mendeley-python-sdk.git#egg=mendeley'
    ]
)
