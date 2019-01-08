import time

import click
from spylogger import get_logger

from protonpack.worker import GhostBuster


logger = get_logger()


@click.group()
@click.pass_context
def worker(ctx):
    pass


@worker.command('startup')
@click.option('-s', '--stream', required=True, help="stream name")
@click.option('-c', '--consumer', required=True, help="consumer group name")
@click.option('-i', '--consumerid', required=True, help="consumer id")
@click.pass_context
def startup(ctx, stream, consumer, consumerid):
    logger.info({
        "message": f"starting up GhostBuster",
        "consumer": consumer,
        "consumerid": consumerid,
        "stream": stream,
    })
    gb = GhostBuster(stream, consumer, consumerid)
    while True:
        gb.do_poll()
        time.sleep(2)
