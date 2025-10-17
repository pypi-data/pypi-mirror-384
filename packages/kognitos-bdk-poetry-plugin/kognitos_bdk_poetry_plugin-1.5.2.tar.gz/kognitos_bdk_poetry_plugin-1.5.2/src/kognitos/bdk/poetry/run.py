import signal
import sys

import docker
from cleo.helpers import option
from poetry.console.commands.command import Command
from poetry.utils.env import EnvManager
from rich import print  # pylint: disable=redefined-builtin
from rich.console import Console

console = Console()


class RunCommand(Command):
    name = "bdk run"
    description = "Run BDK runtime against the current active virtual environment"

    options = [
        option(
            "runtime-version",
            "rv",
            "The version of the BDK runtime to use",
            flag=False,
            default="latest",
            value_required=False,
        ),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._container = None
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, _signal, _frame):
        if self._container is not None:
            console.log("[bold blue]Stopping and removing the container...[/bold blue]")
            self._container.stop()
            self._container.remove()
        console.log("[bold red]Command interrupted! Closing...[/bold red]")
        sys.exit(0)

    def handle(self) -> int:
        runtime_version = self.option("runtime-version")  # get the value of the runtime version

        console.log("[bold blue]Loading up virtual environment...[/bold blue]")
        env = EnvManager(self.poetry).get()
        console.log(f"[bold blue]Virtual Environment: [/bold blue][bold green]{env.path}[/bold green]")

        console.log("[bold blue]Establishing connection with Docker machine...[/bold blue]")
        docker_client = docker.from_env()

        console.log(f"[bold blue]Running Docker container with BDK runtime version {runtime_version}...[/bold blue]")
        self._container = docker_client.containers.run(  # type: ignore
            image=f"719468614044.dkr.ecr.us-west-2.amazonaws.com/kognitos/bdk:{runtime_version}",
            detach=True,
            ports={"8080/tcp": None},
            volumes={str(env.path): {"bind": "/opt/external", "mode": "rw"}},  # type: ignore
            environment={
                "BDK_RUNTIME_PYTHON_BOOK_PATH": "/opt/external/lib/python3.11/site-packages",
                "BDK_RUNTIME_LOG": "debug",
            },
        )

        # print the port mapping
        info = docker_client.api.inspect_container(self._container.id)  # type: ignore
        local_port = info["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"]
        console.log(f"[bold blue]BCI3: [/bold blue][bold green]lambdarie://localhost:{local_port}[/bold green]")

        # interact with the container, print logs continuously
        for log in self._container.logs(stream=True):
            print(log.decode(), end="")

        console.log("[bold blue]Done[/bold blue]")

        return 0
