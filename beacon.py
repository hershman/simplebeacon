#!/usr/bin/env python

import json
import os
import sys
import logging

import _protocol_definitions as beacon_protocol

from flask import *
import ga4gh.protocol as protocol
import ga4gh.client as client

application = app = Flask(__name__)


VARIANTS_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/v0.5.1"

print "Connecting to %s and retrieving variant sets:" % (VARIANTS_URL)
variants_client = client.HttpClient(VARIANTS_URL)
variant_sets_request = protocol.GASearchVariantSetsRequest() #Will need to remove GA soon...
variant_sets = list(variants_client.searchVariantSets(variant_sets_request))
for variant_set in variant_sets:
    print "    %s" % (variant_set.id)


# Beacon Constants/Functions
BEACON_ID = "reference-beacon"
BEACON_NAME = "Beacon"
BEACON_ORGANIZATION = "You"
BEACON_DESCRIPTION = ""
BEACON_AUTH = "OAUTH2" #not true in this file but would be in beacon_rp.py
BEACON_EX_QUERY = "Try searching for A at 1:324532243" #example query
BEACON_EMAIL = "you@blah.com"

def sameAllele(variants, allele):
    """Checks if any variaints have the alternative allele specified"""
    if allele is None:
        return "True"
    for variant in variants:
        if allele == "D":
            if len(variant.referenceBases) > 1:
                return "True"
        else:
            for alternativeBase in variant.alternateBases:
                if allele in alternativeBase:
                    return "True"
    return "False"


@app.route('/')
def app_root():
    return render_template('index.html', variant_sets=variant_sets)


@app.route('/query', methods=['POST'])
def query():
    variant_set_id = request.form['populationId']
    variants_request = protocol.GASearchVariantsRequest() #Will need to remove GA soon...
    variants_request.variantSetIds = [request.form['populationId']]
    variants_request.referenceName = request.form['chrom']
    variants_request.start = int(request.form['position']) - 1  # GA4GH API is zero-based
    variants_request.end = int(request.form['position'])

    variants = variants_client.searchVariants(variants_request)
    exists = sameAllele(variants, request.form['allele'])


    #Make Requrest Response
    request_response = beacon_protocol.ResponseResource()
    request_response.exists = exists
    # request_response also has optional fields: frequency, observed, info, err

    #Make Query
    #we're going to repeat ourselves from above because the beacon response returns the query in a differnt format than a (GA)SearchVariantsRequest
    query_resource = beacon_protocol.QueryResource()
    query_resource.referenceBases = "NA" # (required) reference at this position. I'm not sure where we get this
    query_resource.alternateBases = request.form['allele']
    query_resource.chromosome = request.form['chrom']
    query_resource.position = int(request.form['position']) - 1
    query_resource.reference = "NA" # (required) Another loose end
    query_resource.dataset = request.form['populationId']

    #we now package the request response and query into a BeaconResponseResource
    response = beacon_protocol.BeaconResponseResource()
    response.beacon = BEACON_ID
    response.query = query_resource
    response.response = request_response
    return response.toJsonString()


@app.route('/info', methods=['GET'])
def infoBeacon():
    response = beacon_protocol.BeaconInformationResource()
    response.id = BEACON_ID
    response.name = BEACON_NAME
    response.organization = BEACON_ORGANIZATION
    response.description = BEACON_DESCRIPTION
    response.api = "0.2"
    response.query = BEACON_EX_QUERY
    response.auth = BEACON_AUTH
    response.email = BEACON_EMAIL
    #response.datasets = variant_sets #not correct - there is a specific beacon.avro DataSetResource format expected here
    hostName = os.environ.get("HTTP_HOST", "localhost")
    response.homepage = "http://%s/" % hostName
    return response.toJsonString()

if __name__ == '__main__':
    port = int(os.environ['port']) if 'port' in os.environ else 0xBeac
    app.run(host='0.0.0.0', port=port)



