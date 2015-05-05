# About

This is a very, very basic GA4GH beacon that leverages the GA4GH API reference implementation, version 0.5.1.  It is intentionally simple so that it can be used to experiment with allowing OpenID Connect logins to a beacon.

**DO NOT RUN THIS CODE IN PRODUCTION.**  It is not safe or stable enough for direct exposure to the Internet.  There are likely security issues everywhere.  You have been warned.


## Installation / Running

First, get the GA4GH API demo server working by [following the excellent instructions](http://ga4gh-reference-implementation.readthedocs.org/en/stable/demo.html).  I suggest running the demo under `screen`, but you can always reconnect with a second shell/tty.

This beacon requires flask and the GA4GH python libraries.  The GA4GH API demo utilizes `virtualenv` to compartmentalize these dependencies and we can leverage that hard work.  Just source the `activate` script, as shown in the client example in the demo instructions, cd to the beacon directory, and run it:

```bash
~$ source ga4gh-env/bin/activate
(ga4gh-env) ~$ cd beacon/
(ga4gh-env) ~/beacon$ ./beacon.py
Connecting to http://localhost:8000/v0.5.1 and retrieving variant sets:
    1kg-phase1
    1kg-phase3
```

The beacon will try to connect to `http://localhost:8000/v0.5.1`, anticipating the demo server running on the same machine.  If you have the GA4GH API running on a different host/port, you can use that as the first argument on the command line (it's not very smart about interpreting this, it just concatenates URLs to the end of it):

`$ ./beacon.py https://big-dataset.example.org/v0.5.1` 

The beacon will default to port 48812 (0xbeac), but can also take a port as an environment variable:

`$ port=5000 ./beacon.py`

## TODO

* actually test the installation instructions
* **Beacon v0.2!!!**
* Python3 clean
* Logging (what happened to STDOUT?)
* Return "frequency" in addition to "exists"
* Support ref as a parameter (optional?)
