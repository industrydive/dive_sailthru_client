from setuptools import setup

setup(
    name="dive_sailthru_client",
    version="0.0.6",
    description="Industry Dive abstraction of the Sailthru API client",
    author='David Barbarisi',
    author_email='dbarbarisi@industrydive.com',
    url='https://github.com/industrydive/dive_sailthru_client',
    license='Python',
    zip_safe=False,
    packages=['dive_sailthru_client'],
    install_requires=[
        'sailthru-client==2.3.1',
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'mock']
)
