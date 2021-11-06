#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import json
import logging
import MySQLdb

from confluent_kafka import Producer, Consumer

import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

conf_producer = {'bootstrap.servers': 'kafka1:19092'}
conf_consumer = {'bootstrap.servers': 'kafka1:19092', 'group.id': 'inventory_consumer_group', 'auto.offset.reset': 'earliest'}
producer = Producer(conf_producer)
consumer = Consumer(conf_consumer)

inbound_event_channel = 'inventory'
outbound_success_event_channel = 'payment'
outbound_failure_event_channel = 'order'

db = MySQLdb.connect('127.0.0.1','root','inventorypw', 'inventory')

def process_inventory_reserved(event, transaction_id, inventory_id, quantity):
    logging.info('process_inventory_reserved')
    cursor = db.cursor()
    cursor.execute('UPDATE inventory SET quantity=quantity-%d WHERE id=%d' % (quantity, inventory_id))
    cursor.execute('INSERT INTO inventory_history(transaction_id, inventory_id, quantity) VALUES(\'%s\', %d, %d)' % (transaction_id, inventory_id, -1 * quantity))
    db.commit()
    cursor.execute('SELECT price FROM inventory WHERE id=%d' % inventory_id)
    record = cursor.fetchone()
    cursor.close()

    total_price = int(record[0]) * quantity
    logging.debug('total_price: %d' % total_price)
    event['payment'] = {'total_price': total_price}
    event['status'] = 'INVENTORY_RESERVED'
    producer.produce(outbound_success_event_channel, value=json.dumps(event))

def process_order_cancel(event, transaction_id, inventory_id, quantity):
    logging.info('process_order_cancel')
    cursor = db.cursor()
    cursor.execute('UPDATE inventory SET quantity=quantity+%d WHERE id=%d' % (quantity, inventory_id))
    cursor.execute('INSERT INTO inventory_history(transaction_id, inventory_id, quantity) VALUES(\'%s\', %d, %d)' % (transaction_id, inventory_id, quantity))
    db.commit()
    cursor.close()
    event['status'] = 'ORDER_CANCEL'
    producer.produce(outbound_failure_event_channel, value=json.dumps(event))
    

def main():
    try:
        consumer.subscribe([inbound_event_channel])
        while True:
            message = consumer.poll(timeout=3)
            if message is None:
                continue

            event = message.value()
            if event:
                logging.debug(event)
                evt = json.loads(event)
                status = evt['status']
                transaction_id = evt['transaction_id']
                inventory_id = int(evt['inventory']['id'])
                quantity = int(evt['inventory']['quantity'])

                if status == 'ORDER_CREATED':
                    process_inventory_reserved(evt, transaction_id, inventory_id, quantity)
                elif status == 'ORDER_CANCEL':
                    process_order_cancel(evt, transaction_id, inventory_id, quantity)
                else:
                    logging.error('unknown event')

            else:
                continue

    finally:
        consumer.close()    

if __name__ == '__main__':
    main()
