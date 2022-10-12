import logging
import time
import boto3
import settings
from botocore.exceptions import ClientError

log_format = "%(levelname) -8s %(asctime)s m:%(module)s f:%(funcName)s l:%(lineno)d: %(message)s"
logging.basicConfig(format=log_format)
# Change logging level to DEBUG for more verbose logging
logging.getLogger(__name__).setLevel(logging.INFO)

"""
Purpose:
    A wrapper class for AWS SQS and SNS functions.  This allows us to create some basic
    producer and consumer behavior using Localstack to emulate an AWS environment.

Prerequisites
    - Docker
    - Minikube
    - Kubectl

Additional Information:
    This was mostly taken from the AWS Code Samples documentation, referenced below:

    - https://docs.aws.amazon.com/code-samples/latest/catalog/python-sns-sns_basics.py.html
    - https://docs.aws.amazon.com/code-samples/latest/catalog/python-sqs-message_wrapper.py.html
    - https://docs.aws.amazon.com/code-samples/latest/catalog/python-sqs-queue_wrapper.py.html
"""

class AwsWrapper:
    def __init__(self):
        """
        This will create an AWS Session using our fake AWS credentials.
        This session will be used to create our SQS and SNS resources.
        These resources are then used to trigger AWS API functions like
        creating queues and topics.
        """
        session = boto3.session.Session(
            aws_access_key_id = settings.access_key,
            aws_secret_access_key = settings.secret_access_key,
            region_name = settings.region
        )

        self.sqs = session.resource(
            service_name='sqs', 
            endpoint_url=settings.endpoint_url
        )

    def get_queue(self, name):
        """
        Gets an SQS queue by name.

        :param name: The name that was used to create the queue.
        :return: A Queue object.
        """
        try:
            queue = self.sqs.get_queue_by_name(QueueName=name)
            logging.info("Got queue '%s' with URL=%s", name, queue.url)
        except ClientError as error:
            logging.exception("Couldn't get queue named %s.", name)
            raise error
        else:
            return queue

    @staticmethod
    def receive_messages(queue, max_number, wait_time):
        """
        Receive a batch of messages in a single request from an SQS queue.

        Usage is shown in usage_demo at the end of this module.

        :param queue: The queue from which to receive messages.
        :param max_number: The maximum number of messages to receive. The actual number
                        of messages received might be less.
        :param wait_time: The maximum time to wait (in seconds) before returning. When
                        this number is greater than zero, long polling is used. This
                        can result in reduced costs and fewer false empty responses.
        :return: The list of Message objects received. These each contain the body
                of the message and metadata and custom attributes.
        """
        try:
            messages = queue.receive_messages(
                MessageAttributeNames=['All'],
                MaxNumberOfMessages=max_number,
                WaitTimeSeconds=wait_time
            )
            for msg in messages:
                logging.info("Received message: %s: %s", msg.message_id, msg.body)
        except ClientError as error:
            logging.exception("Couldn't receive messages from queue: %s", queue)
            raise error
        else:
            return messages

    @staticmethod
    def delete_message(message):
        """
        Delete a message from a queue. Clients must delete messages after they
        are received and processed to remove them from the queue.

        Usage is shown in usage_demo at the end of this module.

        :param message: The message to delete. The message's queue URL is contained in
                        the message's metadata.
        :return: None
        """
        try:
            message.delete()
            logging.info("Deleted message: %s", message.message_id)
        except ClientError as error:
            logging.exception("Couldn't delete message: %s", message.message_id)
            raise error
