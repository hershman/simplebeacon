#!/usr/bin/env python

import json
import logging
import os
import sys
import time

from flask import *

from oic.oauth2 import rndstr
from oic.oic import Client
from oic.oic.message import AuthorizationResponse, ProviderConfigurationResponse, RegistrationResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

import ga4gh.protocol as protocol
import ga4gh.client as client

import auth

application = app = Flask(__name__)
app.config['SECRET_KEY'] = open('secret_key', 'rb').read()  # head -c 24 /dev/urandom > secret_key

__OP = json.loads(open('op_config.json').read())

VARIANTS_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/v0.5.1"

print "Connecting to %s and retrieving variant sets:" % (VARIANTS_URL)
variants_client = client.HttpClient(VARIANTS_URL)
variant_sets_request = protocol.GASearchVariantSetsRequest()
variant_sets = list(variants_client.searchVariantSets(variant_sets_request))
for variant_set in variant_sets:
    print "    %s" % (variant_set.id)


@app.route('/')
@auth.require_session(redirect_handler='login')
def index():
    return render_template('index_rp.html', variant_sets=variant_sets, user=session['id'])


@app.route('/query', methods=['POST'])
@auth.require_session(redirect_handler='login')
def query():
    variant_set_id = request.form['populationId']
    variants_request = protocol.GASearchVariantsRequest()
    variants_request.variantSetIds = [request.form['populationId']]
    variants_request.referenceName = request.form['chrom']
    variants_request.start = int(request.form['position']) - 1  # GA4GH API is zero-based
    variants_request.end = int(request.form['position'])

    response = variants_client.searchVariants(variants_request)

    for variant in response:
        for alt in variant.alternateBases:
            if alt == request.form['allele']:
                return "True"
    
    return "False"


@app.route('/login')
def login():
    return render_template('login.html', ops=__OP)


'''
This handles redirecting the user to the OpenID Provider of their choosing.
It constructs the authorization request and redirects the user's browser
to the OP's Authorization Endpoint.

If we want to ask different scopes (ie. custom claims) based on what each
OP supports, this is where that logic would go.  We'd need to query, or know
ahead of time, what claims/scopes each OP understands.
'''
@app.route('/oidc-op-redirect')
def oidc_op_redirect():
    if 'op' in request.args and request.args['op'] in __OP:
        client = __OP[request.args['op']]['client']

        session['op'] = request.args['op']
        session['state'] = rndstr()
        session['nonce'] = rndstr()
        args = {
            "client_id": client.client_id,
            "response_type": "code",
            "scope": ["openid", "email"],
            "nonce": session["nonce"],
            "redirect_uri": client.redirect_uris[0],
            "state": session["state"]
        }
        auth_req = client.construct_AuthorizationRequest(request_args=args)
        login_url = client.authorization_endpoint + "?" + auth_req.to_urlencoded()
        return redirect(login_url)

    return redirect(url_for('login'))

'''
This handles the redirect from the OP once the user has authorized (or not)
access to their identity.  It:

* parses the response
* verifies the opaque state variable matches the browser's session cookie
* performs the out-of-band Access Token request
* possibly performs the out-of-band UserInfo request
* saves the user's email and claim expiry to their session
* redirects the user to the index (hardwired)
'''
@app.route('/oidc-callback')
def oidc_callback():
    client = __OP[session['op']]['client']
    aresp = client.parse_response(AuthorizationResponse, info=request.query_string,
                                  sformat="urlencoded")

    assert aresp["state"] == session["state"]

    args = {
        "code": aresp["code"],
        "redirect_uri": client.redirect_uris[0],
        "client_id": client.client_id,
        "client_secret": client.client_secret
    }

    resp = client.do_access_token_request(scope="openid",
                                          state=aresp["state"],
                                          request_args=args,
                                          authn_method="client_secret_post"
                                          )

    print resp

    # FRAGILE!  Why does do_user_info_request() not authenticate to the OP?
    #    Also, why does the Mitre OP implementation not require that the RP
    #    be authenticated?
    if 'email' in resp['id_token']:
        session['id'] = resp['id_token']['email']
        session['id_expiry'] = resp['id_token']['exp']
    else:
        userinfo = client.do_user_info_request(state=aresp["state"])
        print userinfo
        session['id'] = userinfo['email']
        session['id_expiry'] = resp['id_token']['exp']

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def init_clients():
    for name, op in __OP.iteritems():
        config = json.loads(file('oidc_secrets/%s' % op['config_file']).read())
        client_prefs = {}
        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)

        # Every OP has their own way of expressing their config, this will get unwieldy
        if op['type'] == 'google':
            config = config['web']
 
        client.redirect_uris = config['redirect_uris']
        # Note: store_registration_info() has to happen before provider_config().
        reg_info = {k: config[k] for k in ('client_id', 'client_secret')}
        client.store_registration_info(RegistrationResponse(**reg_info))

        # "/.well-known/openid-configuration" will be added by provider_config()
        client.provider_config(op['config_base'])

        op['client'] = client


if __name__ == '__main__':
    init_clients()
    port = int(os.environ['port']) if 'port' in os.environ else 0xBeac
    app.run(host='0.0.0.0', port=port, debug=True)
