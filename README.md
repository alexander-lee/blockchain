# The Leethereum Blockchain

## Table of Contents

* [Overview](#overview)
  * [Blocks](#blocks)
  * [Transactions](#transactions)
* [Mesh Network](#mesh-network)
  * [Full Client](#full-client)
  * [Miner Client](#miner-client)
  * [SPV Client](#spv-client)
* [Payload Information](#payload-information)

## Overview
This is a proof of concept decentralized blockchain that I created from scratch in order to more deeply understand Blockchain technology.

### Blocks
Blocks have the following structure:
```python
{
  'header': {
    'index': <int>  # indexed from 1 (gross but yes)
    'timestamp': <int>  # number of seconds (since the past epoch)
    'proof': <int>  # the proof of work
    'previous_hash': <str>  # hash of the previous block's header
    'merkleroot': <str>  # the root of the merkle tree given by the transactions
  }
  'transactions': [<transaction hashes>]
  'merkletree': [[<transaction hashes>]]
}
```

### Transactions
Transactions have the following structure:
```python
{
  'previous_hash': <str>  # hash/id of the previous transaction
  'sender': <str>  # address of the sender
  'recipient': <str>  # address of the recipient
  'amount': <int>  # amount in (Leethereum coins) to send
  'timestamp': <int>  # number of seconds (since the past epoch)
}
```

## Mesh Network
All nodes in the mesh network communicate over UDP. Once a node client starts, it sends out a `version` packet with its current blockchain's height. Once other nodes in the network receive a `version` packet, they respond with a `verack` and are ready to start their respective tasks.

Nodes register their peers with the following structure:
```python
{
  'identifier': <str>  # node identifier (for example: 10.0.1.21:node-bjK5NCizt7PkRgaDmTJtdP)
  'lastrecv': <int>  # number of seconds (since the past epoch)
  'lastsend': <int>  # number of seconds (since the past epoch)
  'height': <int>  # current height of the peer's blockchain
}
```

In addition, nodes also send a `heartbeat` packet periodically every 30 minutes to each peer to ensure each peer is still connected. If a `heartbeatack` packet isn't returned then the node will remove the peer from its list of peers.

To run any of the clients, run:

`python3 <client-name>.py`


To receive help/other flags you can use, run:

`python3 <client-name>.py -h`


### Full Client
The Full/Blockchain Client is in charge of storing the entire blockchain and listening for new blocks created by miners. The client is also allowed to create transactions to send to miners.

Once connected, it syncs up with other nodes in order to maintain what it considers the longest/most computationally intense blockchain.

### Miner Client
The Miner Client is in charge of creating blocks with newly verified transactions in the transaction pool. It also stores the entire blockchain and listens for new blocks created by other miners.

The Mining algorithm is very rudimentary in that it runs through a proof of work `p'` from 1 through n until it finds one such that the hash of the previous block's header and `p'` has 5 leading zeros (Difficulty is hard coded).

### SPV Client
The Simplified Payment Verification Client is similar to the Full Client, but it instead only stores block headers.

A feature to work on in the future would be a way to verify transactions using a bloom filter and merkle path that Bitcoin uses for its SPV nodes.

## Payload Information
Nodes in the network can send the following types of packets:
* `version`
  * The initial packet to connect to the network.
  * Comes with a `height` payload specifying the node's blockchain height.
* `verack`
  * Sent by nodes to acknowledge a `version` packet.
* `heartbeat`
  * A heartbeat in order to keep track of peer it is connected to.
* `heartbeatack`
  * Sent by nodes to acknowledge a `heartbeat` packet.
* `getdata`
  * Sent by a node requesting the blockchain.
* `getheaders`
  * Sent by an SPV node requesting the blockchain consisting only of block headers.
* `chain`
  * A packet which consists of the blockchain, sent to the requester of `getdata`.
* `headers`
  * A packet which consists of blockchain headers, sent to the requester of `getheaders`.
* `addblock`
  * Sent by a miner node once a new block has been added to the blockchain.
* `addtx`
  * Sent by a full/SPV node adding a new transaction to the transaction pool so that it can be added into a new block.
* `merkleblock`
  * A packet sent by a Full Node to an SPV Node when a filtered transaction is added to the Blockchain. This packet will send the merkle path and block information in order to allow easy verification.
