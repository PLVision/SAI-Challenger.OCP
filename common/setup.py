from setuptools import setup, find_packages

setup(
    name="saichallenger-common",
    version='0.2',
    description='SAI Challenger core library',
    license='Apache 2.0',
    author='Andriy Kokhan',
    author_email='andriy.kokhan@gmail.com',
    url='https://github.com/PLVision/sai-challenger',
    install_requires=[
        'ptf',
    ],
    packages=find_packages()
)
