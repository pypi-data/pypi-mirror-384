"""Some shortcuts to display rich interface on ikcli."""

import time
from typing import Optional

import rich
import rich.console
import rich.progress
import rich.prompt
import rich.table

import ikcli.net.api
import ikcli.net.http.core
import ikcli.net.http.exceptions
import ikcli.net.http.progress
from ikcli.net.api.pagination import LimitedPagination, Pagination


def table_cell_format(value) -> str:
    """
    Pretty format for table cell.

    Args:
        value: A cell value

    Returns:
        Pretty formatted value
    """
    if value is None:
        return "-"

    # Format value
    if isinstance(value, list):
        fvalue = ",".join(value)
    elif isinstance(value, str):
        fvalue = value
    elif isinstance(value, dict) and "name" in value:
        fvalue = value["name"]
    else:
        fvalue = format(value)

    # Crop data if too long
    if len(fvalue) > 100:
        fvalue = f"{fvalue[:96]} ..."

    return fvalue


def table(pagination: Pagination, title: str, columns: list[str], display: bool = True) -> rich.table.Table:
    """
    Craft (and display) API object in a table.

    Args:
        pagination: Pagination object
        title: Table title
        columns: Column name to display
        display: True if must be display, False otherwise

    Returns:
        Table
    """
    # Define table
    rtable = rich.table.Table()
    for column in columns:
        rtable.add_column(column.replace("_", " ").title(), justify="right")

    # Add row per object
    for row in pagination:
        args = [table_cell_format(row[column]) for column in columns]
        rtable.add_row(*args)

    # If it remains object in pagination, display it
    if isinstance(pagination, LimitedPagination) and pagination.remaining() > 0:
        rtable.add_section()
        rtable.add_row(f"[bold] ... and {pagination.remaining()} remaining")

    # Craft title
    rtable.title = f"{title.title()} ({len(pagination)})"

    # Display if needed
    if display:
        rich.print(rtable)

    # Return table
    return rtable


def menu(title: str, options: dict, prompt: str = "Please choose an option", default=None, none: bool = False):
    """
    Display a menu and ask to user to choose an entry.

    Args:
        title: A menu title
        options: Dict that contains a key to return if chosen and a string to display
        prompt: Prompt to display
        default: A default value
        none: Add a 'None of them' entry to meny

    Returns:
        Selected option key
    """
    # Craft choice list
    choices = sorted(options, key=options.get)
    prompt_choices = [format(i + 1) for i in range(0, len(choices))]
    default_choice = None

    # Define beaufiful padding according to options length
    padding = 1
    if len(choices) >= 10:
        padding = 2
    elif len(choices) >= 100:
        padding = 3

    # Create table menu
    table_menu = rich.table.Table(box=rich.box.MINIMAL_DOUBLE_HEAD)
    table_menu.add_column(title)
    for counter, option in enumerate(choices):
        value = f"{counter+1:{padding}} - {options[option]}"
        if default == option:
            value = "[prompt.default]" + value
            default_choice = counter + 1
        table_menu.add_row(value)

    # If none (of them) is defined, add special entries
    if none:
        options[None] = None
        prompt_choices.append("0")
        choices.append(None)
        table_menu.add_row(f"[bright_black]{0:{padding}} - None of them")

    # Display table and prompt choice
    rich.print(rich.padding.Padding(table_menu, (0, 1)))
    intprompt = rich.prompt.IntPrompt(f" > {prompt}", choices=prompt_choices, show_choices=False)
    intprompt.prompt_suffix = " : "
    index = intprompt(default=default_choice)

    # Return value
    return choices[index - 1]


def create(title: str, api_list: ikcli.net.api.List, *args, **kwargs) -> ikcli.net.api.Object:
    """
    Display spinners and info about object creation.

    Args:
        title: A title to display behind spinner
        api_list: An API list object
        args: Args to create object
        kwargs: Kwargs to create object

    Returns:
        A newly created object
    """
    console = rich.console.Console()
    with console.status(f"[cyan]{title} ..."):
        api_object = api_list.create(*args, **kwargs)
    console.print(f"[green] {api_object}")
    return api_object


def delete(api_object: ikcli.net.api.Object):
    """
    Prompt for object deletion.

    Args:
        api_object: API Object to delete
    """
    console = rich.console.Console()
    if not rich.prompt.Confirm.ask(f"Do you really want to delete [red]'{api_object}'[/red] ?"):
        console.print("[orange3]Aborted by user")
        return

    with console.status(f"[cyan]Deleting {api_object} ..."):
        api_object.delete()
    console.print(f"[orange3]{api_object.__class__.__name__} deleted")


def show_api_object_format(api_object: ikcli.net.api.Object, keys: list[str]) -> list[str]:
    """
    Format an API Object and return a list of str usable by show functions.

    Args:
        api_object: An API Object to format
        keys: Key list name to show

    Yields:
        lines of str for each key
    """
    # For each key
    for key in keys:

        # Get value and format it, according to type
        value = api_object[key]
        if value is None:
            value = "-"
        elif isinstance(value, list):
            value = ",".join(value)

        if key in ["biography", "description"]:
            value = f"\n {value}"

        # Format key to get a fancy result
        key = key.replace("_", " ").title()

        # Yield line
        yield f"[b]{key}[/b]: {value}"


def show(api_object: ikcli.net.api.Object, title: str, keys: list, extra: list = None):
    """
    Display an API Object.

    Args:
        api_object: API Object to show
        title: A title for rich Panel
        keys: A list or object keys to show
        extra: A list of extra things to display. Can be str or rich element.
    """
    # Format object
    lines = list(show_api_object_format(api_object, keys))

    # Append extra display if given
    if extra is None:
        extra = []
    else:
        lines.append("")

    # Render panel
    rich.print(
        rich.panel.Panel(
            rich.padding.Padding(
                rich.console.Group(*lines, *extra),
                (1, 1),
            ),
            title=title,
            width=120,
            border_style="bold white",
        )
    )


def exception(e: Exception):  # pylint: disable=R0912
    """
    Try to properly display exception.

    Args:
        e: Exception to display
    """
    # Process some well known exceptions
    if isinstance(e, ikcli.net.http.exceptions.HTTPBadCodeError):
        title = e.__class__.__name__
        lines = []
        data = e.data()
        if e.code == 401:
            lines.append(
                "\U0001f449 Your API token is not set or expired.\n"
                "May you have to call [red]ikcli login[/red] again or export token as follow:"
            )
            lines.append(
                rich.padding.Padding(
                    "$> export IKOMIA_TOKEN='MyV4ryS3cr3tT0k3n'",
                    (1, 2),
                    style="green on grey11",
                    expand=False,
                ),
            )
        elif isinstance(data, dict) and "errors" in data:
            for error in data["errors"]:
                lines.append(f"\U0001f449 [bright_white]{error['code']}[/bright_white]:")
                for message in error["messages"]:
                    lines.append(f" - {message}")
                if error["metadata"] is not None:
                    lines.append("   [bright_white]Additional information[/bright_white]:")
                    for k, v in error["metadata"].items():
                        lines.append(f"   - {k}: {v}")
                lines.append("")

            # Remove last line return
            lines.pop()
        else:
            lines.append(f"\U0001f449 {data}")
    elif isinstance(e, ikcli.net.api.exceptions.ObjectNotFoundException):
        title = f"{e.object_class.__name__} not found"
        lines = [f"\U0001f449 {e.object_class.__name__} that match :"]
        if len(e.kwargs) > 0:
            lines += [f"  - {k}: '{v}'" for k, v in e.kwargs.items()]
        else:
            lines += ["    *nothing precise*"]
        lines.append("  was not found.")
    elif isinstance(e, ikcli.net.api.exceptions.NotUniqueObjectException):
        title = f"Not unique {e.object_class.__name__} found"
        lines = [f"\U0001f449 {len(e.pagination)} {e.object_class.__name__}(s) that match :"]
        if len(e.kwargs) > 0:
            lines += [f"  - {k}: '{v}'" for k, v in e.kwargs.items()]
        else:
            lines += ["    *nothing precise*"]
        lines.append("  were found :")
        lines += [f"  - {o}" for o in e.pagination]
    else:
        # Common case exception
        title = e.__class__.__name__
        lines = ["\U0001f449 " + str(arg) for arg in e.args]
        if hasattr(e, "__notes__"):  # Officially added to 3.11, but some code part already use it
            lines += [""] + e.__notes__

    # Finally display
    rich.print(
        rich.panel.Panel(
            rich.padding.Padding(rich.console.Group(*lines), (1, 1), style="white"),
            title=title,
            width=80,
            border_style="bold red",
        )
    )


class HTTPTransferProgress(ikcli.net.http.progress.ProgressObserver):
    """A rich progress bar that display http transfer."""

    def __init__(
        self, title: str, http_request: ikcli.net.http.core.HTTPRequest, download: bool = True, upload: bool = False
    ):
        """
        Initialize a new progress bar transfer monitor.

        Args:
            title: Progress bar title
            http_request: HTTPRequest object to monitor.
            download: Display download progress bar.
            upload: Display upload progress bar.
        """
        super().__init__(http_request)
        self.progress = rich.progress.Progress(
            "{task.description} " + title,
            rich.progress.BarColumn(),
            rich.progress.DownloadColumn(),
            rich.progress.TransferSpeedColumn(),
            rich.progress.TimeRemainingColumn(),
        )

        self.progress_upload_task = None
        self.progress_download_task = None

        if upload:
            self.progress_upload_task = self.progress.add_task("[cyan]Uploading", total=None)
        if download:
            self.progress_download_task = self.progress.add_task("[magenta]Downloading", total=None)

    def __enter__(self):
        """Enable progress bar."""
        super().__enter__()
        self.progress.__enter__()

    def __exit__(self, *args):
        """
        Disable progress bar.

        Args:
            *args: stuff given to ContextManager exit function.
        """
        super().__exit__(*args)
        self.progress.__exit__(*args)

    def downloading(self, total: int, completed: int):
        """
        Make download progress bar updated.

        Args:
            total: Total bytes to download
            completed: Already downloaded bytes
        """
        if self.progress_download_task is None:
            return
        self.progress.update(self.progress_download_task, total=total, completed=completed)

    def uploading(self, total: int, completed: int):
        """
        Make upload progress bar updated.

        Args:
            total: Total bytes to upload
            completed: Already uploaded bytes
        """
        if self.progress_upload_task is None:
            return
        self.progress.update(self.progress_upload_task, total=total, completed=completed)


class EndpointProgress(rich.progress.Progress):
    """Override rich progress to easily manage endpoint runs progress."""

    def __init__(self, *args, **kwargs):
        """
        Initialize new EndpointProgress.

        Args:
            *args: args given to rich.progress.Progress
            **kwargs: kwargs given to rich.progress.Progress
        """
        super().__init__(*args, **kwargs)

        # Store rich progress task by run run_id
        self._runs = {}

    def __enter__(self) -> "EndpointProgress":
        """
        Enter on progress context.

        Returns:
            This progress
        """
        self.start()
        return self

    @classmethod
    def get_default_columns(cls) -> tuple[rich.progress.ProgressColumn, ...]:
        """
        Override get_default_columns to fit with endpoint run progress.

        Returns:
            A tuple of default ProgressColumn
        """
        return (
            rich.progress.TextColumn("[progress.description]{task.description}"),
            rich.progress.BarColumn(),
            rich.progress.TimeRemainingColumn(compact=True, elapsed_when_finished=True),
        )

    def add_run_task(self, run_id: str, name: str, short_uuid: str, eta_in_ms: Optional[int], state: str):
        """
        Add a new progress task to track endpoint run progress.

        Args:
            run_id: A run unique id
            name: A name to display on progress bar
            short_uuid: An endpoint run uuid (compact version)
            eta_in_ms: A task estimated time of arrival, in ms
            state: Initial run state
        """
        # Add progress task
        task_id = self.add_task(f"[bright_black]{name}[{short_uuid}] {state}", total=eta_in_ms, start=True)

        # Transform ETA in ms to future timestamp
        if eta_in_ms is not None:
            eta = time.time() + eta_in_ms / 1000
        else:
            eta = None

        # Store info about run
        self._runs[run_id] = {
            "task_id": task_id,
            "eta": eta,
            "start": time.time(),
        }

    def update_all(self):
        """Update all run tasks."""
        now = time.time()
        for runs in self._runs.values():
            completed = (now - runs["start"]) * 1000
            self.update(runs["task_id"], completed=completed, refresh=True)

    def on_progress(self, run_id: str, name: str, uuid: str, state: str, eta: tuple[int, int], **_):
        """
        Endpoint run progress callback function.

        Args:
            run_id: A run unique id
            name: A name to display on progress bar
            uuid: Endpoint run uuid
            state: Endpoint run state (eg: PENDING, SUCCESS, ... )
            eta: A tuple with eta lower bound / upper bound
            **_: Extra and unused parameters
        """
        # Split eta into lower and upper bound
        (eta_lower_bound, eta_upper_bound) = eta

        # Reduce UUID to 8 chars to compact bar description
        if uuid is not None:
            short_uuid = uuid[:8]
        else:
            short_uuid = "--------"

        # Check if it's a new run
        if run_id not in self._runs:
            self.add_run_task(run_id, name, short_uuid, eta_upper_bound, state)
            return

        # If defined, ensure expected ETA is still in bounds
        if eta_upper_bound is not None:

            # Get ETA lower and upper bound as timestamp
            eta_lower_bound_ts = time.time() + eta_lower_bound / 1000
            eta_upper_bound_ts = time.time() + eta_upper_bound / 1000

            # If ETA was previously unset, or if previously calculated ETA is out of new bounds, reset it
            if (
                self._runs[run_id]["eta"] is None
                or self._runs[run_id]["eta"] < eta_lower_bound_ts
                or self._runs[run_id]["eta"] > eta_upper_bound_ts
            ):
                self._runs[run_id]["eta"] = eta_upper_bound_ts
                self.update(
                    self._runs[run_id]["task_id"],
                    total=(self._runs[run_id]["eta"] - self._runs[run_id]["start"]) * 1000,
                )

        # Update description
        description = rich.markup.escape(f"{name}[{short_uuid}] {state}")
        if state == "STARTED":
            description = "[cyan]" + description
        elif state == "SUCCESS":
            description = "[bright_green]" + description
        elif state == "FAILURE":
            description = "[bright_red]" + description
        else:
            description = "[bright_black]" + description
        self.update(self._runs[run_id]["task_id"], description=description)

        # Update all tasks progress
        self.update_all()
