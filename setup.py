import setuptools

long_description = ''
with open('README.md') as readme:
    long_description = readme.read()

setuptools.setup(
    name='yuuki',
    version='1.0.0',
    description='OpenC2 Reference Implementation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/oasis-open/openc2-yuuki',
    packages=setuptools.find_packages(),    
    install_requires=[
        "importlib_resources; python_version < '3.7'",
        "requests >= 2.11.1",
        "Flask >= 0.12.3"],
    package_data={'' : ['*.conf', '*.json']})


