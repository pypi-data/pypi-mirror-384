from setuptools import setup, find_packages

setup(
    name='url_checker_JACK',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    author='JACK',
    description='A simple URL checker library based on \'s public URL.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

