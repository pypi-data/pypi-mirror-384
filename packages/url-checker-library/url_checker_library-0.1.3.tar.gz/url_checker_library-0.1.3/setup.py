from setuptools import setup, find_packages

setup(
    name='url_checker_library',
    version='0.1.3',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    author='JACK',
    author_email='gsksvsksksj@gmail.com',
    description='A library to check URL safety using.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

