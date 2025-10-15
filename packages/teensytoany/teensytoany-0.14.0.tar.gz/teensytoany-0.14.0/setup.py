#!/usr/bin/env python3
from setuptools import find_packages, setup


# Loads _version.py module without importing the whole package.
def get_version_and_cmdclass(pkg_path):
    import os
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location(
        'version', os.path.join(pkg_path, '_version.py'),
    )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.get_cmdclass(pkg_path)


version, cmdclass = get_version_and_cmdclass('teensytoany')

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = ['pyserial', 'packaging', ]

test_requirements = ['pytest', ]

setup(
    author="Ramona Optics Inc.",
    author_email='info@ramonaoptics.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.9',
    description="A pythonic way to access the teensytoany board",
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='teensytoany',
    name='teensytoany',
    entry_points={
        'console_scripts': [
            'teensytoany=teensytoany.cli:teensytoany_cli',
            'teensytoany_programmer=teensytoany.programmer:main',
            'teensytoany_i2c_scan=teensytoany.i2c_scan:main',
            'teensytoany_list=teensytoany.list:main',
        ],
    },
    packages=find_packages(include=['teensytoany']),
    tests_require=test_requirements,
    url='https://github.com/ramonaoptics/python-teensytoany',
    version=version,
    cmdclass=cmdclass,
    zip_safe=False,
)
