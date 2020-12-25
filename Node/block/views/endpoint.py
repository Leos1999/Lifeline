import datetime
import json
from django.shortcuts import render,redirect
import requests

from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse, HttpResponseRedirect

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)


@csrf_exempt
def index(request):
    fetch_posts()
    return render(request,'index.html',{"title":"Patient Information","posts":posts,"node_address":CONNECTED_NODE_ADDRESS})


@csrf_exempt
def submit_textarea(request):
    """
    Endpoint to create a new transaction via our application.
    """
    print(request)
    p_aadhar = request.POST.get("aadhar")
    vacc_id = request.POST.get("vacc_id")
    location = request.POST.get("location")
    h_status = request.POST.get("health_status")

    post_object = {
        'aadhar': p_aadhar,
        'vacc_id': vacc_id,
        'location': location,
        'health_status': h_status
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
