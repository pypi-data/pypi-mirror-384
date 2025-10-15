from setuptools import setup
import pathlib


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="circle-web3-sdk-util",
    version='7.0.0',
    description='The Python SDK Utility for Circle Web3 Services',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/circlefin/circle-web3-python-sdk',
    author='Circle Technology Inc',
    author_email='bohan.li@circle.com',
    classifiers=[],
    keywords='Circle, Web3, Python, Developer Controlled Wallets, User Controlled Wallets, Smart Contract Platform',
    packages=['circle', 'circle.web3'],
    package_dir={'': 'packages'},
    python_requires='>=3.10,<4',
    license='MIT License',
    project_urls={
        'Source': 'https://github.com/circlefin/circle-web3-python-sdk',
        'Developer Doc': 'https://developers.circle.com/w3s/'
    },
    install_requires=[
        'pycryptodome >= 3.20.0',
    ]
)
