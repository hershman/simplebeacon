#!/usr/bin/env python

import json
import os
import sys
import logging

from flask import *
import ga4gh.protocol as protocol
import ga4gh.client as client

application = app = Flask(__name__)


VARIANTS_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/v0.5.1"

print "Connecting to %s and retrieving variant sets:" % (VARIANTS_URL)
variants_client = client.HttpClient(VARIANTS_URL)
variant_sets_request = protocol.GASearchVariantSetsRequest()
variant_sets = list(variants_client.searchVariantSets(variant_sets_request))
for variant_set in variant_sets:
    print "    %s" % (variant_set.id)


@app.route('/')
def app_root():
    return render_template('index.html', variant_sets=variant_sets)


@app.route('/query', methods=['POST'])
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


if __name__ == '__main__':
    port = int(os.environ['port']) if 'port' in os.environ else 0xBeac
    app.run(host='0.0.0.0', port=port)
