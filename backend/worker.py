import logging
import os
import threading
import time

# import the Redis library
import redis
# import the web request library
import requests
# import the tool that loads environment settings
from dotenv import load_dotenv

# load settings from the environment file
load_dotenv()

# name of the Redis stream
STREAM_KEY = "crawl_stream"
# name of the stream for failed messages
DEAD_LETTER_KEY = "crawl_stream:dead"
# name shared by all workers in one group
GROUP_NAME = "crawl_workers"
# name that identifies this worker
CONSUMER_NAME = "worker-1"
# address of the api that receives each document
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/documents/crawl")

# time before an unconfirmed message is considered stuck
IDLE_TIMEOUT_MS = 30_000
# number of times a message may be delivered
MAX_ATTEMPTS = 3
# seconds between checks for stuck messages
RECLAIM_INTERVAL_SECONDS = 10

# set the format and detail level for log messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# create a logger named worker
logger = logging.getLogger("worker")

# connect to Redis using the address in the environment settings
redis_client = redis.from_url(os.getenv("REDIS_URL"), socket_timeout=10, decode_responses=True)


def ensure_group():
    # try to create the Redis group used to share messages
    try:
        # use the stream and group names defined above
        # start reading from the beginning and create the stream if needed
        redis_client.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    # Redis reports setup problems with a ResponseError
    except redis.exceptions.ResponseError as exc:
        # an existing group gives the BUSYGROUP error which is safe to ignore
        if "BUSYGROUP" not in str(exc):
            # raise a different error because it may show a real problem
            raise


def handle_message(msg_id, fields):
    # send one message to the api
    try:
        # send the message fields as json data
        response = requests.post(API_URL, json=fields)
        # turn an unsuccessful response into an error
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # record the failure and leave the message unconfirmed for a retry
        logger.warning(f"failed to process {msg_id} ({fields.get('url')}): {exc}")
        return
    # tell Redis that the message was handled successfully
    redis_client.xack(STREAM_KEY, GROUP_NAME, msg_id)
    # record the successful processing
    logger.info(f"processed {fields.get('url')}")


def dead_letter(msg_id):
    # find the original message in the main stream
    entries = redis_client.xrange(STREAM_KEY, min=msg_id, max=msg_id)
    # continue only when the message still exists
    if entries:
        # take the message data from the Redis result
        _id, fields = entries[0]
        # copy the failed message to the dead letter stream
        redis_client.xadd(DEAD_LETTER_KEY, fields)
        # record that the message will not be tried again
        logger.error(f"dead-lettered {msg_id} ({fields.get('url')}) after {MAX_ATTEMPTS} attempts")
    # remove the message from the group pending list
    redis_client.xack(STREAM_KEY, GROUP_NAME, msg_id)


def reclaim_loop():
    # keep checking for messages that need another attempt
    while True:
        # wait before checking again
        time.sleep(RECLAIM_INTERVAL_SECONDS)

        # get a summary of messages waiting for confirmation
        pending_summary = redis_client.xpending(STREAM_KEY, GROUP_NAME)
        # record the total stream size and pending message count
        logger.info(f"queue depth: {redis_client.xlen(STREAM_KEY)} total, {pending_summary['pending']} pending")

        # find messages that have been waiting longer than the timeout
        stuck = redis_client.xpending_range(
            STREAM_KEY, GROUP_NAME, min="-", max="+", count=100, idle=IDLE_TIMEOUT_MS
        )
        # check each stuck message
        for entry in stuck:
            # get the message id from the Redis result
            msg_id = entry["message_id"]
            # get the number of times Redis has delivered the message
            attempts = entry["times_delivered"]
            # send messages with too many attempts to the dead letter stream
            if attempts >= MAX_ATTEMPTS:
                dead_letter(msg_id)
                continue
            # give the message to this worker for another attempt
            claimed = redis_client.xclaim(
                STREAM_KEY, GROUP_NAME, CONSUMER_NAME, min_idle_time=IDLE_TIMEOUT_MS, message_ids=[msg_id]
            )
            # process every message returned by Redis
            for claimed_id, fields in claimed:
                # record that the message is being tried again
                logger.warning(f"retrying {claimed_id} ({fields.get('url')}), attempt {attempts + 1}")
                # send the message to the api
                handle_message(claimed_id, fields)


def run():
    # make sure the stream and group exist
    ensure_group()
    # start checking for stuck messages in the background
    threading.Thread(target=reclaim_loop, daemon=True).start()

    # keep waiting for new messages
    while True:
        # ask Redis for one new message and wait up to five seconds
        response = redis_client.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=1, block=5000)
        # try again when no message arrived during the wait
        if not response:
            continue
        # go through each stream returned by Redis: main & dead letters
        for _stream_key, messages in response:
            # go through the messages in the stream
            for msg_id, fields in messages:
                # process the message
                handle_message(msg_id, fields)


if __name__ == "__main__":
    # start the worker when this file is run directly
    run()
