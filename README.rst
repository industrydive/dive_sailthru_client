Dive Sailthru Client
====================

Industry Dive abstraction of the Sailthru API Client.

This is intended to be a drop-in replacement for the official client at <https://github.com/sailthru/sailthru-python-client>. That means it preserves all the original API functions (though some are improved with e.g. better error detection) and adds some new features, namely better exception handling for all API functions plus some new functions to conveniently request campaign metadata annotated with a guess on the type of email it is and the dive publication (misnamed as key `dive_brand`) it refers to.

Running tests
-----------------------------
You can run a test suite for this client in both py2 and py3 by doing `make test`

If you have issues using the make command for running tests,
first set the environment variables in the command line with the following command:

export SAILTHRU_API_KEY="place key for dev account here" .   

export SAILTHRU_API_SECRET="place secret for dev account here"

then run the following command to execute the tests:

python setup.py test


Changelog
-----------------------------
v0.0.23 - added HalfBlast email type