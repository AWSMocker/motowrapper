from setuptools import setup

setup(
    py_modules=['aws_moto_wrapper.wrapper'],
    entry_points={
        'pytest11': [
            'moto-wrapper-plugin = aws_moto_wrapper.wrapper',
        ],
    },
)
