from setuptools import setup, find_packages
import os

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
	'Topic :: Software Development :: Libraries :: Python Modules',
	'Development Status :: 4 - Beta',
    'Topic :: Security :: Cryptography',
]

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
REQUIREMENTS = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).read().split()





setup(
    author='Luis Zarate',
    author_email='luis.zarate@solvosoft.com',
    name='dfva-python',
    version='0.0.7',
    description='DFVA client for python.',
    long_description=README,
    url='https://github.com/luisza/dfva_python',
    license='GNU General Public License v3 (GPLv3)',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=REQUIREMENTS,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    long_description_content_type='text/x-rst'
    
)

