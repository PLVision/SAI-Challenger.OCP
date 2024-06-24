from setuptools import setup, find_packages

setup(
    name="saichallenger",
    version='0.1',
    description='SAI Challenger CLI & basic topologies',
    license='Apache 2.0',
    author='Andriy Kokhan',
    author_email='andriy.kokhan@gmail.com',
    url='https://github.com/PLVision/sai-challenger',
    install_requires=[
        'click==8.0',
    ],
    packages=find_packages(),
    scripts=[
        'scripts/redis-cmd-listener.py'
    ],
    entry_points={
        'console_scripts': [
            'sai = cli.main:cli',
        ]
    },
)
