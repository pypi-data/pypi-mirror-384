from typing import List
from confclasses import confclass, unused, from_dict
import traceback
import logging
from confclasses.exceptions import ConfclassesMissingValueError
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.tree  import Tree
from rich.prompt import Prompt
from rich.live import Live

console = Console()
logger = logging.getLogger(__name__)

# 2 sets of defaults in this file, inside each action and in the SetupDefinitions default values, as sometimes it makes sense to have different defaults
# - The default in the action classes are for when the action is defined in a definitions file but no value is provided for that attribute
# - The default in the SetupDefinitions is for when the definitions file is not provided

# decorator to register the actions, saves having to do it manually. Lets also add confclasses here, saves space
actions = {}
modules = set()
def action(cls=None):
    def wrap(cls):
        cls = confclass(cls)
        actions[cls.action_name] = cls
        modules.add(cls.__module__)
        return cls
    return wrap(cls) if cls else wrap

@confclass
class SetupDefinition:
    action: str

@confclass
class SetupDefinitions:
    definitions: List[SetupDefinition] = [
        {"action": "base.conf-dir"},
        {"action": "base.conf-file", "merge": True},
        {"action": "ssh.host-keygen"},
    ]

    def __post_init__(self):
        self.execution_plan = []

    def get_action_cls(self, name: str):
        module = name.split(".")[0]
        if module not in modules:
            __import__(f"{__package__}.actions.{module}", fromlist=[module])
            modules.add(module)
        
        return actions[name]

    def add_definition_to_plan(self, name: str, tree: Tree, indent=1):
        if name in self.execution_plan:
            return

        action_cls = self.get_action_cls(name)

        for dep in getattr(action_cls, "action_depends", []):
            self.add_definition_to_plan(dep, tree=tree.add(f"{dep}"), indent=indent+1)

        self.execution_plan.append(name)

    def make_action(self, name: str, args: dict):
        try:
            action = self.get_action_cls(name)()
            from_dict(action, args)
            return action
        except ConfclassesMissingValueError as e:
            if len(e.missing) > 2:
                raise Exception(f"Nested missing values are not supported") from e
            missing_key = e.missing[1]
            value = Prompt.ask(f"[yellow]{name} requires user input for '{missing_key}'[/yellow]")
            args[missing_key] = value
            return self.make_action(name, args)

    def panel_wrapper(self, title: str, func: callable):
        log = []
        panel = Panel(Text("Pending..."), title=title, style="cyan")
        with Live(panel, console=console, refresh_per_second=4) as live:
            gen = func()
            try:
                while True:
                    log.append(next(gen))
                    panel.renderable = Group(*log)
                    live.update(panel)
            except StopIteration as e:
                success = e.value  # <- final return value
                panel.title += "Success" if success else "Failed"
                panel.style = "bold green" if success else "bold red"
                live.update(panel)
                return success

    def run(self):
        action_args = {}
        dependency = Tree("Setup Actions", style="cyan")
        panel = Panel(dependency, title="Building Dependency Tree for Setup")
        for definition in self.definitions:
            item = dependency.add(f"{definition.action}")
            self.add_definition_to_plan(definition.action, tree=item)
            action_args[definition.action] = unused(definition)
        console.print(panel)

        execution_plan = []
        text = Text()
        panel = Panel(text, title="Execution Order")
        for idx, action_name in enumerate(self.execution_plan):
            text.append(f"\n[{idx}] {action_name}", style="cyan")
            action = self.make_action(action_name, action_args.get(action_name, {}))
            execution_plan.append(action)
            if hasattr(action, "pre"):
                if not self.panel_wrapper(
                    title=f"Pre {action.action_name}",
                    func=action.pre
                ):
                    break
        console.print(panel)

        for action in execution_plan:
            if not self.panel_wrapper(
                title=action.action_name,
                func=action.run
            ):
                break
