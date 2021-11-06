#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import uuid
import json
import logging
from datetime import datetime

import sys
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.expressions.update import Action

from confluent_kafka import Consumer

conf_consumer = {'bootstrap.servers': 'kafka1:19092', 'group.id': 'order_consumer_group', 'auto.offset.reset': 'earliest'}
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

def process_payment_complete(model):
    model.update(actions=[OrderModel.status.set('ORDER_COMPLETE')])
    logging.info('Entire order transaction completed')

def process_order_cancel(model):
    model.update(actions=[OrderModel.status.set('ORDER_CANCEL')])
    logging.info('Order cancelled')


def main():
    try:
        consumer.subscribe(['order'])
        while True:
            message = consumer.poll(timeout=3)
            if message is None:
                continue
            event = message.value()
            if event:
                evt = json.loads(event)
                transaction_id = evt['transaction_id']
                user_id = evt['order']['user_id']
                status = evt['status']
                model = OrderModel(transaction_id, user_id)

                if status == 'PAYMENT_COMPLETE':
                    process_payment_complete(model)
                elif status == 'ORDER_CANCEL':
                    process_order_cancel(model)
                else:
                    logging.error('unknown event')
            else:
                continue

    finally:
        consumer.close()    

if __name__ == '__main__':
  main()
