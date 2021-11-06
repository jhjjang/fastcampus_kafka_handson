#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import uuid
import json
import logging
from datetime import datetime

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

from flask import Flask, request, jsonify

from confluent_kafka import Producer, Consumer

import sys
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

conf_producer = {'bootstrap.servers': 'kafka1:19092'}
conf_consumer = {'bootstrap.servers': 'kafka1:19092', 'group.id': 'cousumer_group', 'auto.offset.reset': 'earliest'}
producer = Producer(conf_producer)
consumer = Consumer(conf_consumer)


class OrderModel(Model):
    class Meta:
        table_name = 'order'
        host = 'http://localhost:4566'
        region = 'us-east-2'

    transaction_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    name = UnicodeAttribute(null=True)
    addr = UnicodeAttribute(null=True)
    tel = UnicodeAttribute(null=True)
    email = UnicodeAttribute(null=True)
    status = UnicodeAttribute(null=True)
    updated = UTCDateTimeAttribute()

if not OrderModel.exists():
    OrderModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)


app = Flask(__name__)

@app.route('/v1/order', methods=['GET'])
def show_transaction():
    transaction_id = request.args.get('transaction_id')
    user_id = request.args.get('user_id')
    try:
        order = OrderModel.get(transaction_id, user_id)
        return jsonify(order.attribute_values)
    except OrderModel.DoesNotExist:
        return jsonify({'error': 'data not found'})


@app.route('/v1/order', methods=['POST'])
def create_order():
    entire_req = json.loads(request.data)
    req = entire_req['order']

    transaction_id = str(uuid.uuid1())
    user_id = req['user_id']
    name = req['name']
    addr = req['addr']
    tel = req['tel']
    email = req['email']

    model = OrderModel(transaction_id, user_id)
    model.updated = datetime.now()
    model.status = 'ORDER_CREATED'
    model.save()

    entire_req['transaction_id'] = transaction_id
    entire_req['status'] = model.status

    logging.debug("entire_req: %s" % entire_req) 
    producer.produce('inventory', value=json.dumps(entire_req))
    producer.flush()
    return jsonify({'status': model.status,
                    'user_id': user_id,
                    'transaction_id': transaction_id})    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
