from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.style import StyleType

import os
if os.name == "nt":
    from ssm_cli.selectors.tui.win import getch, UP, DOWN, CTRL_C, ENTER
else:
    from ssm_cli.selectors.tui.posix import getch, UP, DOWN, CTRL_C, ENTER

console = Console()

class TableWithArrows(Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_row = 0

    def up(self):
        if self._selected_row > 0:
            self._selected_row -= 1

    def down(self):
        if self._selected_row < len(self.rows) - 1:
            self._selected_row += 1

    def get_row_style(self, console: "Console", index: int) -> StyleType:
        style = super().get_row_style(console, index)
        if index == self._selected_row:
            style += console.get_style("on blue")
        return style

def select(instances: list):
    table = TableWithArrows(title="Instances")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Ping")
    table.add_column("IP")
    for instance in instances:
        table.add_row(
            instance.id,
            instance.name,
            instance.ping,
            instance.ip,
        )

    with Live(table, console=console, auto_refresh=False) as live:
        while True:
            live.update(table, refresh=True)
            ch=getch()
            if ch == UP:
                table.up()
            elif ch == DOWN:
                table.down()
            elif ch == CTRL_C:  # Ctrl+C
                raise KeyboardInterrupt()
            elif ch == ENTER:  # Enter key (carriage return or newline)
                break
            else:
                print(repr(ch))

    return instances[table._selected_row]
