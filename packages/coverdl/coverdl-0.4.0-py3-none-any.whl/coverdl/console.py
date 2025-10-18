import click

class Console:
    def __init__(self, silence_warnings: bool) -> None:
        self.silence_warnings = silence_warnings

    def warn(self, message: str):
        if self.silence_warnings:
            return
        click.echo(f"{click.style('Warn:', fg='yellow')} {message}")

    def error(self, message: str):
        click.echo(f"{click.style('Error:', fg='red')} {message}")

    def echo(self, *args, **kwargs):
        click.echo(*args, **kwargs)
