# About

This is a very, very basic GA4GH beacon that leverages the GA4GH API reference implementation, version 0.5.1.  It is intentionally simple so that it can be used to experiment with allowing OpenID Connect logins to a beacon.

**DO NOT RUN THIS CODE IN PRODUCTION.**  It is not safe or stable enough for direct exposure to the Internet.  There are likely security issues everywhere.  You have been warned.


## Installation / Running

**All instructions are for Ubuntu Server 14.04 amd64, tested on an AWS micro instance.  YMMV.**


First, get the GA4GH API demo server working by [following the excellent instructions](http://ga4gh-reference-implementation.readthedocs.org/en/stable/demo.html).  I suggest running the demo under `screen`, but you can always reconnect with a second shell/tty.

This beacon requires flask and the GA4GH python libraries.  The GA4GH API demo utilizes `virtualenv` to compartmentalize these dependencies and we can leverage that hard work.

### Without OpenID Connect

Just source the `activate` script, as shown in the client example in the demo instructions, cd to the beacon directory, and run it:

```bash
~$ source ga4gh-env/bin/activate
(ga4gh-env) ~$ cd simplebeacon/
(ga4gh-env) ~/simplebeacon$ ./beacon.py
Connecting to http://localhost:8000/v0.5.1 and retrieving variant sets:
    1kg-phase1
    1kg-phase3
```

The beacon will try to connect to `http://localhost:8000/v0.5.1`, anticipating the demo server running on the same machine.  If you have the GA4GH API running on a different host/port, you can use that as the first argument on the command line (it's not very smart about interpreting this, it just concatenates URLs to the end of it):

`$ ./beacon.py https://big-dataset.example.org/v0.5.1` 

The beacon will default to port 48812 (0xbeac), but can also take a port as an environment variable:

`$ port=5000 ./beacon.py`


### With OpenID Connect

Getting this beacon working as an OpenID Connect Relying Party still requires the use of the GA4GH API demo server, so like the non-OpenID Connect version, you need to start by [installing the GA4GH API demo server](http://ga4gh-reference-implementation.readthedocs.org/en/stable/demo.html) and running `ga4gh_server` in a different shell (better to use `screen`).

Supporting OpenID Connect requires a few additional installed packages as well as running an HTTPS-capable webserver.  The webserver is up to you but I suggest nginx in proxy mode (ie. `proxy_pass http://127.0.0.1:48812;`), which should suffice for testing and experimentation.

We'll rely on the "oic" package to provide OpenID Connect functionality for us.  This package includes support for the "Javascript Object Signing and Encryption" (JOSE) framework, an integral part of OpenID Connect.  The package that supplies this support, "jwkest", has a few global-level dependencies.  We'll start with those and then get the python packages installed.  You should do this in the virtualenv you set up earlier:

```bash
~$ source ga4gh-env/bin/activate
(ga4gh-env) ~$ sudo apt-get install libffi-dev libssl-dev
...a whole lot of installation stuff...
(ga4gh-env) ~$ pip install oic
...even more installation stuff...
Successfully installed oic pycrypto pyjwkest mako beaker alabaster pyOpenSSL future cryptography idna pyasn1 enum34 ipaddress cffi pycparser
Cleaning up...
(ga4gh-env) ~$
```

Great!  Everything is installed!  But before running the OpenID Connect Relying Party ("RP") version of the beacon you'll need to register your beacon with an OpenID Connect Provider ("OP"), put your Client ID and secret in `oidc_secrets` in the form of a JSON doc, and create an entry to that OP config in `op_config.json`.

If you're looking for an OP to test against, Google's Identity API supports OpenID Connect, is free, and is pretty simple to set up.  [Here's some instructions with screenshots here](doc/setup_google_identity.md).  Put the JSON containing your Client ID and secret in `oidc_secrets`.  Better yet, put it somewhere safe and create a symlink to it from `oidc_secrets`.  (You shouldn't ever need to write these documents by hand but I've included examples of these two types in the `oidc_secrets` directory for reference.)

OpenID Connect doesn't specify a schema for expressing Client ID/secret documents, so you'll need to specify what `type` of OP you got the file from in `op_config.json`.  I've added support for two JSON formats: the one produced by [Google's Identity API](https://developers.google.com/identity/protocols/OpenIDConnect) (`"type": "google"`), and the one produced by [MITREid Connect](http://kit.mit.edu/projects/mitreid-connect) (`"type": "mitre"`).

You'll need to make an entry for the OP in `op_config.json`.  I've included `op_config.example.json`, which has examples showing the two different types.  For each entry there is:

* `type` - Describes the schema of the JSON containing the Client ID and secret. Valid values are "google" or "mitre" for now.
* `config_file` - The filename of the JSON containing the Client ID and secret, relative to the `oidc_secrets` directory.
* `name` - The name of the OP.  _This will show in the interface._
* `description` - Simple text description of the OP.  _This will show in the interface._
* `logo` - Logo filename, relative to the images directory in `static`.  _This will show in the interface._
* `config_base` - A URL that is used for dynamic configuration of the OP.  The code currently uses the `.well-known/openid-configuration` endpoint on OPs to discover auth and token endpoints, keys, etc.  This saves the considerable effort of having an elaborate config for each OP in `op_config.json` (most of this information is not in the Client ID/secret JSON you downloaded).  If you're interested in seeing what this dynamic configuration looks like, [check out Google's version](https://accounts.google.com/.well-known/openid-configuration).

One last configuration detail: you'll need 24 bytes of randomness that Flask will use as a secure cookie.  You can create that with `head -c 24 /dev/urandom > secret_key` in the same directory as the beacon.

If everything is configured correctly, things should work similarly to running it without OpenID Connect.  Just source the `activate` script, as shown in the client example in the demo instructions, cd to the beacon directory, and run it:

```bash
~$ source ga4gh-env/bin/activate
(ga4gh-env) ~$ cd simplebeacon/
(ga4gh-env) ~/simplebeacon$ head -c 24 /dev/urandom > secret_key  # for secure cookies
(ga4gh-env) ~/simplebeacon$ ./beacon_rp.py
Connecting to http://localhost:8000/v0.5.1 and retrieving variant sets:
    1kg-phase1
    1kg-phase3
```


## Caveats

* The OP configuration is a bit fragile and will need refactoring as we get more experience with OPs
* The OpenID RP code only supports static registration.  As we don't recommend dynamic registration, this is unlikely to change.
* Once the user's identity is established the server doesn't bother with refresh tokens, but it does respect the expiration time of the claim.  This means when expiry happens the system will brutally redirect you to the logout page.
* The callback selectively calls the UserInfo endpoint, which is compensation for `do_user_info_request()` not authenticating the client.


## TODO

* **Beacon v0.2!!!**
* Better results page
* Python3 clean
* Logging (what happened to STDOUT?)
* Return "frequency" in addition to "exists"
* Support ref as a parameter (optional?)
* Add nginx/uwsgi configs
