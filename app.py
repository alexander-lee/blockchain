from flask import Flask, jsonify, request
from uuid import uuid4

from blockchain import Blockchain

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # 1. Find the Proof of work
    # 2. Add current_transactions to a new block
    # 3. Reward the miner
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Create a special transaction which acts as the reward for the miner
    # TODO: Change amount so it decreases over time
    blockchain.add_transaction(
        sender='0',
        recipient=node_identifier,
        amount='1'
    )

    previous_hash = last_block['previous_hash']
    block = blockchain.add_block(proof, previous_hash)

    response = {
        'message': 'New Block created',
        'hash': Blockchain.hash(block),
        'block': block,
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Validate Request
    required_fields = ['sender', 'recipient', 'amount']
    for field in required_fields:
        if field not in values:
            return f'{field} is missing!', 400

    # Create transaction
    new_index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    response = {'message': f'Transaction will be added to block {new_index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
