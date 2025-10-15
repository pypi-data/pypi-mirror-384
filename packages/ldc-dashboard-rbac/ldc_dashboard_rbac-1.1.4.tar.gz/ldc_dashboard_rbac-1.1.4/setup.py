import os
from setuptools import setup, find_packages

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='ldc-dashboard-rbac',
    version='1.1.4',
    description='A backend-only Django app for feature-based role-based access control (RBAC)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Nishant Baruah',
    author_email='nishant.baruah@lendenclub.com',
    url='https://github.com/nishantbaruahldc/ldc-dashboard-rbac',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Security',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
    ],
    keywords='django rbac permissions features groups access-control backend',
    python_requires='>=3.8',
    project_urls={
        'Bug Reports': 'https://github.com/nishantbaruahldc/ldc-dashboard-rbac/issues',
        'Source': 'https://github.com/nishantbaruahldc/ldc-dashboard-rbac',
        'Documentation': 'https://ldc-dashboard-rbac.readthedocs.io/',
    },
)