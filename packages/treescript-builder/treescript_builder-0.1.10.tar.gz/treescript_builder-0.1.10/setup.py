"""Setup Build Configuration
"""
from setuptools import find_packages, setup


setup(
    name="treescript-builder",
    version="0.1.10",
    description='Builds File Trees from TreeScript. If DataLabels are present in TreeScript, a DataDirectory argument is required.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="DK96-OS",
	url='https://github.com/DK96-OS/treescript-builder',
	project_urls={
        "Issues": "https://github.com/DK96-OS/treescript-builder/issues",
        "Source Code": "https://github.com/DK96-OS/treescript-builder",
	},
    license="GPLv3",
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={
        'console_scripts': [
            'ftb=treescript_builder.__main__:main',
            'treescript-builder=treescript_builder.__main__:main',
        ],
    },
    python_requires='>=3.11',
    keywords=['TreeScript', 'Files', 'Directory'],
    classifiers=[
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
)
