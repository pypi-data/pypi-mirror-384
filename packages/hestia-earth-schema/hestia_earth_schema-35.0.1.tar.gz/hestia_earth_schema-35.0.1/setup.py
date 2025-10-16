from setuptools import find_namespace_packages, setup


with open('docs/python.md', 'r') as fh:
    long_description = fh.read()


setup(
    name='hestia_earth_schema',
    version='35.0.1',
    description='HESTIA Schema library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Guillaume Royer',
    author_email='guillaumeroyer.mail@gmail.com',
    license='MIT',
    url='https://gitlab.com/hestia-earth/hestia-schema',
    keywords=['hestia', 'schema'],
    classifiers=[],
    packages=find_namespace_packages(include=['hestia_earth.*']),
    install_requires=[],
    python_requires='>=3.12'
)
