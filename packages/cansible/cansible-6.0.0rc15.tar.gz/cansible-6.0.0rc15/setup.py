from setuptools import setup


setup(
    name='cansible',
    version='6.0.0rc15',
    setup_requires='setupmeta',
    packages=['cansible'],
    install_requires=[
        'cli2',
        'ansible',
    ],
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/cli2',
    include_package_data=True,
    license='MIT',
    keywords='cli',
    python_requires='>=3.6',
    entry_points={
        'pytest11': [
            'cansible-fixtures = cansible.pytest',
        ],
    },
)
