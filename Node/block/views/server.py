from django.shortcuts import render
import requests
from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse


import datetime
import json
from hashlib import sha256
import time


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @staticmethod
    def proof_of_work(block):
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        return len(self.unconfirmed_transactions) >= 2

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []

        return True


blockchain = Blockchain()
blockchain.create_genesis_block()

peers = set()

# 1


def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)

# 2
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

@csrf_exempt
def new_transaction(request):
    tx_data = json.loads(request.body)
    required_fields = ['aadhar', 'vacc_id', 'location']

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    time_to_mine = blockchain.add_new_transaction(tx_data)
    if time_to_mine:
        mine_unconfirmed_transactions()
    return HttpResponse("Success", 201)

# 3


def get_chain(request):
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    response = json.dumps({"length": len(chain_data),
                           "chain": chain_data,
                           "peers": list(peers)})
    return JsonResponse(response)

# 4


@csrf_exempt
def register_new_peers(request):
    node_address = json.loads(request.body)["node_address"]
    if not node_address:
        return HttpResponse("Invalid data", 400)
    peers.add(node_address)
    return get_chain(request)

# 5


@csrf_exempt
def register_with_existing_node(request):
    node_address = json.loads(request.body)["node_address"]
    if not node_address:
        return HttpResponse("Invalid data", 400)
    print(request.build_absolute_uri())
    data = {"node_address": request.build_absolute_uri()}
    headers = {"Content-Type": "application/json"}

    response = requests.post(node_address + "register_new_peers/",
                             data=json.dumps(data), headers=headers)
    print(response)
    if response.status_code == 200:
        global blockchain
        global peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return HttpResponse("Registration successful", 200)
    else:
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain

# 6


@csrf_exempt
def verify_and_add_block(request):
    block_data = json.loads(request.body)
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return HttpResponse("The block was discarded by the node", 400)

    return HttpResponse("Block added to the chain", 201)

# 7





def consensus():
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)
