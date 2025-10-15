from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("VERSION", "r", encoding="utf-8") as f:
    version = f.read()

setup(
    name='talisman-domain',
    version=version,
    description='Talisman domain implementations',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='ISPRAS Talisman NLP team',
    author_email='modis@ispras.ru',
    maintainer='Vladimir Mayorov',
    maintainer_email='vmayorov@ispras.ru',
    packages=find_packages(include=['tie_domain', 'tie_domain.*']),
    install_requires=[
        'talisman-interfaces>=0.8,<0.12', 'talisman-api~=1.3', 'talisman-dm>=1.3.1,<2',
        'typing_extensions>=4.0.0'
    ],
    entry_points={
        'talisman.plugins': ['domain = tie_domain']
    },
    data_files=[('', ['VERSION'])],
    package_data={
        'tie_domain.domain.api._impl': ['graphql/**/*']
    },
    python_requires='>=3.10',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License'
    ]
)
