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

        self.sns = session.resource(
            service_name='sns', 
            endpoint_url=settings.endpoint_url
        )

    def create_queue(self, name, attributes=None):
        """
        Creates an Amazon SQS queue.

        :param name: The name of the queue. This is part of the URL assigned to the queue.
        :param attributes: The attributes of the queue, such as maximum message size or
                        whether it's a FIFO queue.
        :return: A Queue object that contains metadata about the queue and that can be used
                to perform queue operations like sending and receiving messages.
        """
        if not attributes:
            attributes = {}

        try:
            queue = self.sqs.create_queue(
                QueueName=name,
                Attributes=attributes
            )
            logging.info("Created queue '%s' with URL=%s", name, queue.url)
        except ClientError as error:
            logging.exception("Couldn't create queue named '%s'.", name)
            raise error
        else:
            return queue

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

    def create_topic(self, name):
        """
        Creates a notification topic.

        :param name: The name of the topic to create.
        :return: The newly created topic.
        """
        try:
            topic = self.sns.create_topic(Name=name)
            logging.info("Created topic %s with ARN %s.", name, topic.arn)
        except ClientError:
            logging.exception("Couldn't create topic %s.", name)
            raise
        else:
            return topic

    def list_topics(self):
        """
        Lists topics for the current account.

        :return: An iterator that yields the topics.
        """
        try:
            topics_iter = self.sns.topics.all()
            logging.info("Got topics.")
        except ClientError:
            logging.exception("Couldn't get topics.")
            raise
        else:
            return topics_iter

    @staticmethod
    def subscribe(topic, protocol, endpoint):
        """
        Subscribes an endpoint to the topic. Some endpoint types, such as email,
        must be confirmed before their subscriptions are active. When a subscription
        is not confirmed, its Amazon Resource Number (ARN) is set to
        'PendingConfirmation'.

        :param topic: The topic to subscribe to.
        :param protocol: The protocol of the endpoint, such as 'sms' or 'email'.
        :param endpoint: The endpoint that receives messages, such as a phone number
                         (in E.164 format) for SMS messages, or an email address for
                         email messages.
        :return: The newly added subscription.
        """
        try:
            subscription = topic.subscribe(
                Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
            logging.info("Subscribed %s %s to topic %s.", protocol, endpoint, topic.arn)
        except ClientError:
            logging.exception(
                "Couldn't subscribe %s %s to topic %s.", protocol, endpoint, topic.arn)
            raise
        else:
            return subscription

    @staticmethod
    def publish_message(topic, message, attributes):
        """
        Publishes a message, with attributes, to a topic. Subscriptions can be filtered
        based on message attributes so that a subscription receives messages only
        when specified attributes are present.

        :param topic: The topic to publish to.
        :param message: The message to publish.
        :param attributes: The key-value attributes to attach to the message. Values
                           must be either `str` or `bytes`.
        :return: The ID of the message.
        """
        try:
            att_dict = {}
            for key, value in attributes.items():
                if isinstance(value, str):
                    att_dict[key] = {'DataType': 'String', 'StringValue': value}
                elif isinstance(value, bytes):
                    att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value}
            response = topic.publish(Message=message, MessageAttributes=att_dict)
            message_id = response['MessageId']
            logging.info(
                "Published message with attributes %s to topic %s.", attributes,
                topic.arn)
        except ClientError:
            logging.exception("Couldn't publish message to topic %s.", topic.arn)
            raise
        else:
            return message_id