import click

# from protonpack.service import app


@click.group()
@click.pass_context
def service(ctx):
    pass


@service.command('subscriber-list')
@click.pass_context
def startup(ctx):
    print("not yet implemented")
