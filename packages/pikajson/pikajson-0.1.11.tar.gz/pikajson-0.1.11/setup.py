from setuptools import setup, find_packages
from os.path import join, dirname
import pikajson

setup(
    name='pikajson',
    version=pikajson.__version__,
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    install_requires=[
        'pika'
    ],
    author="EvgrDan",
    url="https://zvonobot.ru"
)