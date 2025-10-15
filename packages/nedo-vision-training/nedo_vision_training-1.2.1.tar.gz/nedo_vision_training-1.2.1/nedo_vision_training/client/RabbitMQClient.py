import time
import pika
import json
from nedo_vision_training.logger.Logger import Logger

class RabbitMQClient:
    def __init__(self, config=None, heartbeat=60, blocked_connection_timeout=300, name="default"):
        """
        Initializes RabbitMQClient with connection parameters.
        
        :param config: Dictionary containing RabbitMQ connection details.
        :param heartbeat: Heartbeat interval for RabbitMQ.
        :param blocked_connection_timeout: Timeout for blocked connections.
        :param name: Identifier for the RabbitMQ client instance.
        """
        self.host = config['rabbitmq_host']
        self.port = int(config['rabbitmq_port'])
        self.username = config['rabbitmq_username']
        self.password = config['rabbitmq_password']
        self.heartbeat = heartbeat
        self.blocked_connection_timeout = blocked_connection_timeout
        self.connection = None
        self.channel = None
        self.name = name
        self.logger = Logger(f"RABBITMQ:{name}")

        if not hasattr(self, 'initialized'):
            self.initialized = True

    def connect(self, max_retries=5, backoff_factor=2):
        """Attempts to establish a connection to RabbitMQ with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                self.logger.info(f"🔌 Establishing connection to RabbitMQ ({self.name})...")
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials,
                    heartbeat=self.heartbeat,
                    blocked_connection_timeout=self.blocked_connection_timeout
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.logger.info(f"✅ Connection to RabbitMQ ({self.name}) established successfully.")
                return
            except pika.exceptions.AMQPConnectionError as e:
                retries += 1
                delay = backoff_factor ** retries
                self.logger.error(f"❌ RabbitMQ connection error: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            except pika.exceptions.ProbableAuthenticationError as e:
                self.logger.error(f"🔑 Authentication failed: {e}")
                raise
            except Exception as e:
                retries += 1
                delay = backoff_factor ** retries
                self.logger.error(f"⚠️ Unexpected error while connecting to RabbitMQ: {e}. Retrying in {delay}s...")
                time.sleep(delay)

        raise ConnectionError("❌ Failed to connect to RabbitMQ after maximum retries.")

    def close(self):
        """Closes the RabbitMQ connection and channel if open."""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
        except Exception as e:
            self.logger.warning(f"⚠️ Error closing channel: {e}")
            
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            self.logger.warning(f"⚠️ Error closing connection: {e}")
            
        self.logger.info(f"🔒 RabbitMQ ({self.name}) connection closed.")

    def declare_exchange(self, exchange_name, exchange_type='direct', durable=True):
        """Declares an exchange in RabbitMQ."""
        try:
            self.channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)
            self.logger.info(f"✅ Exchange '{exchange_name}' declared successfully.")
        except Exception as e:
            self.logger.error(f"❌ Error declaring exchange '{exchange_name}': {e}")
            raise

    def declare_queue(self, queue_name, durable=True, auto_delete=False):
        """Declares a queue in RabbitMQ."""
        try:
            self.channel.queue_declare(queue=queue_name, durable=durable, auto_delete=auto_delete)
            self.logger.info(f"🎯 Queue '{queue_name}' declared successfully.")
        except Exception as e:
            self.logger.error(f"❌ Error declaring queue '{queue_name}': {e}")
            raise

    def bind_queue(self, exchange_name, queue_name, routing_key):
        """Binds a queue to an exchange with a routing key."""
        try:
            self.channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
            self.logger.info(f"✅ Queue '{queue_name}' bound to exchange '{exchange_name}' with routing key '{routing_key}'.")
        except Exception as e:
            self.logger.error(f"❌ Error binding queue '{queue_name}' to exchange '{exchange_name}': {e}")
            raise

    def publish_message(self, exchange_name, routing_key, message):
        """Publishes a message to an exchange."""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message
            )
            if exchange_name != 'airosentris.status':
                self.logger.info(f"📤 Message published to exchange '{exchange_name}' with routing key '{routing_key}'.")
        except pika.exceptions.StreamLostError as e:
            self.logger.error(f"⚠️ Stream lost, attempting to reconnect: {e}")
            self.connect()
            self.publish_message(exchange_name, routing_key, message)
        except Exception as e:
            self.logger.error(f"❌ Error publishing message: {e}")
            raise

    def consume_messages(self, queue_name, on_message_callback, auto_ack=False):
        """Starts consuming messages from a specified queue."""
        try:
            self.logger.info(f"📩 Listening for messages in queue '{queue_name}'. Press CTRL+C to exit.")
            self.channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback, auto_ack=auto_ack)
            self.channel.start_consuming()
            self.logger.info("🛑 Message consumption stopped.")
        except pika.exceptions.AMQPConnectionError as e:
            self.logger.error(f"⚠️ Connection error during message consumption: {e}")
            self.connect()
            self.consume_messages(queue_name, on_message_callback, auto_ack)
        except pika.exceptions.StreamLostError as e:
            self.logger.error(f"⚠️ Stream lost, attempting to reconnect: {e}")
            self.connect()
            self.consume_messages(queue_name, on_message_callback, auto_ack)
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during message consumption: {e}")
            raise

    def stop_consuming(self):
        """Stops message consumption."""
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
            self.logger.info("🛑 Stopped consuming messages.")
