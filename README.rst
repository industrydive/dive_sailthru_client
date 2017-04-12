Dive Sailthru Client
====================

Industry Dive abstraction of the Sailthru API Client.

This is intended to be a drop-in replacement for the official client at <https://github.com/sailthru/sailthru-python-client>. That means it preserves all the original API functions (though some are improved with e.g. better error detection) and adds some new features, namely better exception handling for all API functions plus some new functions to conveniently request campaign metadata annotated with a guess on the type of email it is and the dive brand it refers to.
