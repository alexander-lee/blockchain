from flask import Flask
from uuid import uuid4

import blockchain as Blockchain

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
