from setuptools import setup, find_packages
import codecs, os.path

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='pdfix-sdk',
    author='PDFix s.r.o.',
    version=get_version("src/pdfixsdk/__init__.py"),
    author_email='support@pdfix.net',
    description='PDFix SDK - Automated PDF Remediation, Data Extraction, HTML Conversion',
    keywords='pdfix, pdf, accessibility, remediation, extraction, html, conversion, render, watermark, redact, sign, forms',
    long_description=long_description,
    long_description_content_type='text/markdown',
    zip_safe=False,
    url='https://github.com/pdfix/pdfix-sdk-pypi-package',
    project_urls={
        'Documentation': 'https://github.com/pdfix/pdfix-sdk-pypi-package',
        'Bug Reports': 'https://github.com/pdfix/pdfix-sdk-pypi-package/issues',
        'Source Code': 'https://github.com/pdfix/pdfix-sdk-pypi-package',
        "Homepage" : "https://pdfix.net",
        "License" : "https://pdfix.net/terms"
    },
    package_dir={'': 'src'},
    package_data={'pdfixsdk': ['bin/arm64/*', 'bin/x86_64/*', 'bin/aarch64/*', 'bin/x86/*']},
    packages=find_packages(where='src'),
    classifiers=[
        # see https://pypi.org/classifiers/
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=['requests'],
    extras_require={
        'dev': ['check-manifest'],
        # 'test': ['coverage'],
    }
    # entry_points={
    #     'console_scripts': [  # This can provide executable scripts
    #         'run=examplepy:main',
    # You can execute `run` in bash to run `main()` in src/examplepy/__init__.py
    #     ],
    # },
)
