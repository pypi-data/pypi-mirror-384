'''
    out - Simple logging with a few fun features.
    © 2018-25, Mike Miller - Released under the LGPL, version 3+.
'''
import sys
from os.path import dirname, join
from setuptools import setup


if sys.version_info.major < 3:
    raise NotImplementedError('Sorry, only Python 3 and above is supported.')


# additional metadata, requirements
keywords = 'log logging events levels color terminal console standard out err '
install_requires = (
    'console>=0.9912b1',
)
tests_require = ('pyflakes', 'readme_renderer'),
extras_require = dict(
    highlight=('pygments>=2.4.0',),
)


def get_version(filename, version='1.00'):
    ''' Read version as text to avoid machinations at import time. '''
    with open(filename) as infile:
        for line in infile:
            if line.startswith('__version__'):
                try:
                    version = line.split("'")[1]
                except IndexError:
                    pass
                break
    return version


def slurp(filename):
    try:
        with open(join(dirname(__file__), filename), encoding='utf8') as infile:
            return infile.read()
    except FileNotFoundError:
        pass  # needed at upload time, not install time


setup(
    name                = 'out',
    description         = 'Fun take on logging for non-huge projects.'
                          ' Gets "outta" the way.',
    author_email        = 'mixmastamyk@github.com',
    author              = 'Mike Miller',
    keywords            = keywords,
    license             = 'LGPL 3',
    long_description    = slurp('README.rst'),
    long_description_content_type = 'text/x-rst',
    packages            = ('out',),
    url                 = 'https://github.com/mixmastamyk/out',
    version             = get_version('out/__init__.py'),

    extras_require      = extras_require,
    install_requires    = install_requires,
    python_requires     = '>=3.8',
    setup_requires      = install_requires,
    tests_require       = tests_require,

    classifiers         = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
)
