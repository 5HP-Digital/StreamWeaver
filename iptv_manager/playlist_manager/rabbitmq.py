"""
RabbitMQ utility for message publishing.
"""

import json
import pika
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_rabbitmq_connection():
    """
    Create and return a connection to RabbitMQ.
    
    Returns:
        pika.BlockingConnection: A connection to RabbitMQ.
    """
    try:
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER, 
            settings.RABBITMQ_PWD
        )
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials
        )
        return pika.BlockingConnection(parameters)
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        raise

def publish_message(queue_name, message):
    """
    Publish a message to a RabbitMQ queue.
    
    Args:
        queue_name (str): The name of the queue to publish to.
        message (dict): The message to publish.
        
    Returns:
        bool: True if the message was published successfully, False otherwise.
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare the queue (creates it if it doesn't exist)
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Publish the message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        
        connection.close()
        logger.info(f"Message published to queue '{queue_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to publish message to RabbitMQ: {str(e)}")
        return False