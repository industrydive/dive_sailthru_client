from setuptools import setup, find_packages

setup(
    name = "dive_sailthru_client",
    version = "0.0.1",
    zip_safe=False,
    packages=['dive_sailthru_client'],
    install_requires=[
        'sailthru-client==2.2.0',
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'mock']
)
