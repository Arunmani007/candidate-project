import time
import logging
from multiprocessing import Process
from server import Server
from http.server import HTTPServer
from aws_wrapper import AwsWrapper

# Set up logging config and format
def setup_logging():
    log_format = "%(levelname) -8s %(asctime)s m:%(module)s f:%(funcName)s l:%(lineno)d: %(message)s"
    logging.basicConfig(format=log_format)
    # Change logging level to DEBUG for more verbose logging
    logging.getLogger().setLevel(logging.INFO)

# Set up web server for health endpoint
def setup_health_check():

    webServer = HTTPServer(('', 5000), Server)
    logging.info("Server started on port 5000!")
    webServer.serve_forever()

def create_infrastructure():
    aws_wrapper = AwsWrapper()

    ## Create an initial topic
    topic = aws_wrapper.create_topic('local_topic')

    ## Create an initial queue
    queue = aws_wrapper.create_queue(
        'local_queue',
        {
            'MaximumMessageSize': str(1024),
            'MessageRetentionPeriod': str(60)
        }
    )

    ## Add a subscription
    aws_wrapper.subscribe(topic, 'sqs', queue.url)

    ## Return wrapper client to handle messages.
    return aws_wrapper

def publish_messages():

    # Set up logging
    setup_logging()

    logging.info("Creating initial infrastructure...")
    aws_wrapper = create_infrastructure()

    logging.info("Preparing to publish messages...")
    # Grab newly created topic
    topics = aws_wrapper.list_topics()
    topic = None

    for item in topics:
        logging.info(f'Topic: {item}')
        topic = item

    # Loop and publish messages
    while True:
        message = f'Hello from Ibotta! The time is now {time.ctime()}.'
        logging.info(f'Outgoing Message: {message}')

        try:
            message_id = aws_wrapper.publish_message(topic, message, attributes={})
            logging.info(f'Publish success! SNS MessageId: {message_id}')
        except Exception:
            # Log stack trace of error
            logging.error(f'Error occurred! Printing stack trace!', exc_info=True)

        # Sleep in between executions
        time.sleep(10)

if __name__ == '__main__':
    setup_logging()
    Process(target = publish_messages).start()
    Process(target = setup_health_check).start()