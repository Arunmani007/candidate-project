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

# Sets up logging, gets our queue, and starts processing messages.
def process_messages():
    print("Preparing to processing messages...")

    # Get our queue object
    aws_wrapper = AwsWrapper()
    queue = aws_wrapper.get_queue('local_queue')

    # Loop and receive messages
    while True:
        try:
            messages = aws_wrapper.receive_messages(queue, 1, 5)

            for message in messages:
                aws_wrapper.delete_message(message)

        except Exception:
            # Log stack trace of error
            logging.error(f'Error occurred! Printing stack trace!', exc_info=True)

        # Sleep in between executions
        time.sleep(5)

if __name__ == '__main__':
    setup_logging()
    Process(target = process_messages).start()
    Process(target = setup_health_check).start()