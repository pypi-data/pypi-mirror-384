from setuptools import setup, find_packages

setup(
    name='SpamKit', 
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'user-agent',
    ],
    author='JACK',
    author_email='gsksvsksksj@gmail.com',
    description='A utility library for sending emails (legitimate use).',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)