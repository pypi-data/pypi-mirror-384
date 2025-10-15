# Importing necessary modules
import os
import json
import logging
from confluent_kafka import Producer

def find_project_root(start_path: os.PathLike[str] = None):
    """
    Finds the root directory of a project by searching for specific marker files or folders, 
    such as a `.git` folder or `setup.py` file, which commonly indicate the root of a repository.

    Args:
        start_path (os.PathLike[str], optional): The starting path for the search. Defaults to the current working 
            directory if not specified.

    Returns:
        Optional[os.PathLike[str]]: The absolute path to the project root if found, otherwise None.
    """
    if start_path is None:
        start_path = os.getcwd()
        
    current_path: os.PathLike[str] = start_path
    while current_path != os.path.dirname(current_path):
        if os.path.isdir(os.path.join(current_path, '.git')):
            return current_path
        if os.path.isfile(os.path.join(current_path, 'setup.py')):
            return current_path
        current_path = os.path.dirname(current_path)
        
    return None

# KafkaHandler - Class
class KafkaLoggingHandler(logging.Handler):
    """
    Custom logging handler for publishing log records to a Kafka topic.

    This handler integrates with the Confluent Kafka producer to send
    JSON-formatted log entries to a specified Kafka topic. It supports
    retry and failover mechanisms to ensure reliability across multi-broker
    Kafka clusters.

    Attributes:
        producer (Producer): Configured Kafka producer instance.
        topic (str): Kafka topic where log messages are published.
    """

    def __init__(self, bootstrap_servers: str, topic: str = 'emp-logs'):
        """
        Initializes the KafkaLoggingHandler with a resilient Kafka producer.

        Args:
            bootstrap_servers (str): Comma-separated list of Kafka broker addresses.
            topic (str, optional): Kafka topic name for log publishing.
                Defaults to 'emp-logs'.
        """
        super().__init__()
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'acks': 'all',
            'retries': 5,
            'retry.backoff.ms': 300,
            'socket.timeout.ms': 10000,
            'message.send.max.retries': 5,
            'request.timeout.ms': 15000,
            'enable.idempotence': True,
            'queue.buffering.max.ms': 500,
            'max.in.flight.requests.per.connection': 5
        })
        self.topic = topic

    def delivery_report(self, err, msg):
        """
        Kafka delivery callback for asynchronous message acknowledgment.

        Args:
            err (Exception | None): The error if message delivery failed, otherwise None.
            msg (Message): The Kafka message object that was produced.

        Behavior:
            - Logs an error message if delivery failed.
            - Does nothing if the delivery was successful.
        """
        if err is not None:
            logging.getLogger(name = 'KafkaLoggingHandler').error(f'Delivery failed: {err}')

    def emit(self, record: logging.LogRecord):
        """
        Publishes a log record to the configured Kafka topic.

        Args:
            record (logging.LogRecord): The log record to be published.

        Behavior:
            - Formats the log record.
            - Sends the record to Kafka using the configured producer.
            - Handles any Kafka-related errors gracefully by logging them
              through a local fallback logger.
        """
        try:
            log_entry = self.format(record=record)
            self.producer.produce(
                self.topic,
                key = record.name,
                value = log_entry.encode(encoding = 'utf-8'),
                on_delivery = self.delivery_report
            )
            self.producer.poll(0)
        except Exception as e:
            logging.getLogger(name = 'KafkaLoggingHandler').error(f'Kafka emit error: {e}')

# Function to create custom logger
def setup_logger(
    SERVICE: str,
    module: str = 'Serverless'
) -> logging.Logger:
    """
    Creates and configures a structured, environment-aware logger for EMP services.

    This function initializes a JSON-formatted logger named `<SERVICE>-<module>` that adapts 
    its output destination based on the active environment. In local development (`dev`), logs 
    are written to rotating files under `./logs/`. In higher environments (`int`, `stg`, `prd`), 
    logs are published directly to Kafka for centralized aggregation and analysis.

    Example:
        ```python
        logger = setup_logger(SERVICE='Location', module='Serverless')
        logger.info('Logger initialized successfully')
        ```

    Behavior:
        - **dev** → Logs written to local files in overwrite (`w`) mode.  
        - **int/stg/prd** → Logs sent to Kafka topic `emp-logs` via `KafkaLoggingHandler`.  
        - Automatically creates a `logs` directory if it does not exist.  
        - Log entries follow a standardized JSON format compatible with ELK Stack and other observability tools.

    Log format:
        ```json
        {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "thread": "%(threadName)s",
            "logger": "%(name)s",
            "service": "<SERVICE>",
            "environment": "<ENVIRONMENT>",
            "message": "%(message)s"
        }
        ```

    Args:
        SERVICE (str): Name of the service or microservice (e.g., "Customer", "Location").
        module (str, optional): Logical module or component name within the service. Defaults to "Serverless".

    Returns:
        logging.Logger: A fully configured logger instance, ready for structured application logging.
    """
    
    # Setting up the environment
    ENVIRONMENT: str = os.getenv(key = 'ENVIRONMENT', default = 'dev')
    
    # Ensuring Logger Root
    logger_name = f'{SERVICE}-{module}'
    if logger_name in logging.root.manager.loggerDict:
        return logging.getLogger(name = logger_name)

    logger = logging.getLogger(name = logger_name)
    logger.setLevel(level = logging.INFO)
    logger.propagate = False

    # Log format (consistent with logback-spring.xml)
    formatter = logging.Formatter(json.dumps({
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "thread": "%(threadName)s",
        "logger": "%(name)s",
        "service": SERVICE,
        "environment": ENVIRONMENT,
        "message": "%(message)s"
    }))

    # Define log directory (for local environments)
    ROOT_DIR = find_project_root() or os.getcwd()
    log_dir = os.path.join(ROOT_DIR, 'logs')
    os.makedirs(name = log_dir, exist_ok = True)
    log_file_path = os.path.join(log_dir, f'EMP-{SERVICE}-{module}_{ENVIRONMENT}.log')

    # Decide which handler to use
    if ENVIRONMENT.lower() in ('int', 'stg', 'prd'):
        # Kafka handler
        kafka_servers = os.getenv(key = 'KAFKA_BOOTSTRAP_SERVERS', default = 'emp-kafka-1:9092,emp-kafka-2:9093,emp-kafka-3:9094')
        kafka_handler = KafkaLoggingHandler(bootstrap_servers = kafka_servers)
        kafka_handler.setFormatter(fmt = formatter)
        logger.addHandler(hdlr = kafka_handler)
    else:
        # Local file handler
        log_mode = 'a' if ENVIRONMENT.lower() in ('stg', 'prd') else 'w'
        file_handler = logging.FileHandler(filename = log_file_path, mode = log_mode, delay = True)
        file_handler.setFormatter(fmt = formatter)
        logger.addHandler(hdlr = file_handler)

    return logger