import time

import click

from protonpack.worker import GhostBuster


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
    gb = GhostBuster(stream, consumer, consumerid)
    while True:
        gb.do_poll()
        time.sleep(2)
