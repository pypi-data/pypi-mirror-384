from setuptools import find_packages
from setuptools import setup

setup(

    name='Power_Qt',

    author='Dominick Gagliano',

    author_email='dgaglian96@gmail.com',

    version='0.1.0',
    description='A python library for generalized Qt models for PyQt6',
    long_description="Eventually I'll add a description",

    long_description_content_type="text/markdown",
    url='https://github.com/Squidu/Power_Qt',
    install_requires=['superqt>=0.7.6',
                      'pandas~=2.3.2',
                      'numpy~=2.3.2',
                      'sympy~=1.14.0',
                      'polars~=1.33.1',
                      'Pint~=0.25',
                      'matplotlib~=3.10.6',
                      'setuptools~=80.9.0',
                      ],

    packages=find_packages(),

    python_requires='>=3.10,<3.13',

    classifiers=[

        # I can say what phase of development my library is in.
        'Development Status :: 4 - Beta',

        # Here I'll add the audience this library is intended for.
        'Intended Audience :: Developers',

        # Here I'll define the license that guides my library.
        'License :: OSI Approved :: MIT License',

        # Here I'll note that package was written in English.
        'Natural Language :: English',

        # Here I'll note that any operating system can use it.
        'Operating System :: Microsoft :: Windows',

        # Here I'll specify the version of Python it uses.
        'Programming Language :: Python :: 3.10',

        # Here are the topics that my library covers.


    ]

)
