from setuptools import setup, find_packages

setup(
    name='devforge',
    version='1.0.0',
    author='Hythm Saad',
    author_email='hythmsaadkhalifa@email.com',
    description='A smart CLI tool to generate project structures instantly.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/hythm/devforge',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'devforge=devforge.cli:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
