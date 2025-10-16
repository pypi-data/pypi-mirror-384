import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self, TypedDict

from kevinbotlib.exceptions import (
    CommandSchedulerAlreadyExistsException,
    CommandSchedulerDoesNotExistException,
)
from kevinbotlib.logger import Logger as _Logger


class Command(ABC):
    """Synchronous command interface that users will implement"""

    @abstractmethod
    def init(self) -> None:
        """Ran once when the command is initialized."""

    @abstractmethod
    def execute(self) -> None:
        """Ran continuously while the command is active."""

    @abstractmethod
    def end(self) -> None:
        """Ran once when the command is finished."""

    @abstractmethod
    def finished(self) -> bool:
        """
        Get if the command has finished execution.

        Returns:
            True if the command is finished, False otherwise.
        """
        return False

    def then(self, next_command: "Command") -> "SequentialCommand":
        """
        Chain commands to run sequentially

        Args:
            next_command: Command to run next

        Returns:
            Sequential Command
        """

        commands = self.startup_commands if isinstance(self, SequentialCommand) else [self]
        commands.append(next_command)
        return SequentialCommand(commands)

    def alongside(self, next_command: "Command") -> "ParallelCommand":
        """
        Chain commands to run in parallel

        Args:
            next_command: Command to run alongside this command.

        Returns:
            Parallel Command
        """

        commands = self.startup_commands if isinstance(self, ParallelCommand) else [self]
        commands.append(next_command)
        return ParallelCommand(commands)


class _SequencedCommand(TypedDict):
    command: Command
    has_init: bool


class SequentialCommand(Command):
    def __init__(self, commands: list[Command]) -> None:
        """
        Construct a new sequential command.

        Args:
            commands: List of commands to run sequentially.
        """

        super().__init__()
        self.startup_commands = commands
        self.remaining_commands: list[_SequencedCommand] = [
            {"command": command, "has_init": False} for command in commands
        ]

    def init(self) -> None:
        self.remaining_commands: list[_SequencedCommand] = [
            {"command": command, "has_init": False} for command in self.startup_commands
        ]

    def execute(self) -> None:
        current_command = self.remaining_commands[0]
        if not current_command["has_init"]:
            current_command["command"].init()
            current_command["has_init"] = True

        current_command["command"].execute()

        if current_command["command"].finished():
            current_command["command"].end()
            self.remaining_commands.pop(0)

    def end(self) -> None:
        pass

    def finished(self) -> bool:
        return len(self.remaining_commands) == 0


class ParallelCommand(Command):
    def __init__(self, commands: list[Command]) -> None:
        """
        Construct a new parallel command.

        Args:
            commands: Commands to run in parallel.
        """

        super().__init__()
        self.startup_commands = commands
        self.remaining_commands: list[_SequencedCommand] = [
            {"command": command, "has_init": False} for command in commands
        ]

    def init(self) -> None:
        self.remaining_commands = [{"command": command, "has_init": False} for command in self.startup_commands]

    def execute(self) -> None:
        for command_info in self.remaining_commands[:]:
            command = command_info["command"]
            if not command_info["has_init"]:
                command.init()
                command_info["has_init"] = True

            command.execute()

            if command.finished():
                command.end()
                self.remaining_commands.remove(command_info)

    def end(self) -> None:
        for command_info in self.remaining_commands:
            command_info["command"].end()

    def finished(self) -> bool:
        return len(self.remaining_commands) == 0


class ConditionallyForkedCommand(Command):
    def __init__(self, condition: Callable[[], bool], command_met: Command, command_unmet: Command) -> None:
        """
        Construct a new conditionally forked command.

        Args:
            condition: Choose which command to run based on a condition.
            command_met: Command to run if the condition is met.
            command_unmet: Command to run if the condition is not met.
        """

        super().__init__()
        self.command_met = command_met
        self.command_unmet = command_unmet
        self.condition = condition
        self.running_command: Command | None = None

    def init(self) -> None:
        self.running_command = self.command_met if self.condition() else self.command_unmet
        self.running_command.init()

    def execute(self) -> None:
        if self.running_command:
            self.running_command.execute()

    def end(self) -> None:
        if self.running_command:
            self.running_command.end()

    def finished(self) -> bool:
        finished = self.running_command.finished() if self.running_command else False
        if finished:
            self.running_command = None
        return finished


@dataclass
class TriggerActions:
    """Trigger types to be used internally within the command scheduler"""

    on_true: Command | None = None
    """Triggers when a value becomes True"""

    on_false: Command | None = None
    """Triggers when a value becomes False"""

    while_true: Command | None = None
    """Triggers while a value is True"""

    while_false: Command | None = None
    """Triggers while a value is False"""


class Trigger:
    def __init__(self, trigger_func: Callable[[], bool], command_system: "CommandScheduler"):
        """
        Create a new Command trigger.

        Args:
            trigger_func: Function that returns the value that is polled in the scheduler loop.
            command_system: Command scheduler instance to apply the trigger.
        """

        self.trigger_func = trigger_func
        self.command_system = command_system
        self.last_state: bool | None = None
        self.actions = TriggerActions()

    def check(self) -> tuple[bool, bool, Callable[[], bool]]:
        """
        Check the current state of the trigger and determine if it has changed. To be used internally within the scheduler lopp.

        Returns:
            Current state and whether it has changed since the last check.
        """

        current_state = self.trigger_func()
        changed = current_state != self.last_state
        self.last_state = current_state
        return current_state, changed, self.trigger_func

    def on_true(self, command_instance: Command) -> "Trigger":
        """
        Trigger a command once when a condition is met.

        Args:
            command_instance: Command to trigger.

        Returns:
            This trigger
        """

        self.actions.on_true = command_instance
        self.command_system.register_trigger(self)
        return self

    def on_false(self, command_instance: Command) -> "Trigger":
        """
        Trigger a command once when a condition is unmet.

        Args:
            command_instance: Command to trigger.

        Returns:
            This trigger
        """

        self.actions.on_false = command_instance
        self.command_system.register_trigger(self)
        return self

    def while_true(self, command_instance: Command) -> "Trigger":
        """
        Trigger a command once and keep running while a condition is met.

        Args:
            command_instance: Command to trigger.

        Returns:
            This trigger
        """

        self.actions.while_true = command_instance
        self.command_system.register_trigger(self)
        return self

    def while_false(self, command_instance: Command) -> "Trigger":
        """
        Trigger a command once and keep running while a condition is unmet.

        Args:
            command_instance: Command to trigger.

        Returns:
            This trigger
        """

        self.actions.while_false = command_instance
        self.command_system.register_trigger(self)
        return self


class _ScheduledCommand(TypedDict):
    command: Command
    trigger: Trigger | None
    has_init: bool


class CommandScheduler:
    instance: Self | None = None
    overrun_time: float = 0.01
    trigger_overrun_time: float = 0.005

    def __init__(self) -> None:
        """Create a new Command Scheduler."""

        if CommandScheduler.instance:
            msg = "Another instance of CommandScheduler is running"
            raise CommandSchedulerAlreadyExistsException(msg)

        self._scheduled: list[_ScheduledCommand] = []
        self._triggers: list[Trigger] = []

    @staticmethod
    def get_instance() -> "CommandScheduler":
        """
        Get the singleton instance of the CommandScheduler.

        Returns:
            CommandScheduler instance.
        """

        if CommandScheduler.instance:
            return CommandScheduler.instance
        raise CommandSchedulerDoesNotExistException

    @property
    def command_overrun(self) -> float:
        """
        Get the amount of time in seconds that the scheduler will execute a command that will cause an overrun warning
        Returns:
            Overrun time in seconds.
        """
        return CommandScheduler.overrun_time

    @command_overrun.setter
    def command_overrun(self, value: float) -> None:
        """
        Set the amount of time in seconds that the scheduler will execute a command that will cause an overrun warning
        Args:
            value: Overrun time in seconds.
        """
        CommandScheduler.overrun_time = value

    @property
    def trigger_overrun(self) -> float:
        """
        Get the amount of time in seconds that the scheduler will check a trigger that will cause an overrun warning
        Returns:
            Overrun time in seconds.
        """
        return CommandScheduler.overrun_time

    @trigger_overrun.setter
    def trigger_overrun(self, value: float) -> None:
        """
        Set the amount of time in seconds that the scheduler will check a trigger that will cause an overrun warning
        Args:
            value: Overrun time in seconds.
        """
        CommandScheduler.trigger_overrun_time = value

    def schedule(self, command: Command) -> None:
        """
        Manually schedule a command to run.

        Args:
            command: Command to schedule.
        """

        self._schedule(command, None)

    def register_trigger(self, trigger: Trigger) -> None:
        """
        Register a new command trigger. To be used internally in `Trigger`.

        Args:
            trigger: Trigger to register.
        """

        self._triggers.append(trigger)

    def _schedule(self, command: Command, trigger: Trigger | None):
        self._scheduled.append({"command": command, "trigger": trigger, "has_init": False})

    def iterate(self) -> None:
        """
        Executes one iteration of the command scheduler, processing all scheduled commands
        and their triggers according to their current state and conditions.
        """

        # Get trigger states, determine if the command should be run
        for trigger in self._triggers:
            start_check_time = time.monotonic()
            current_state, state_changed, func = trigger.check()
            end_check_time = time.monotonic()

            if end_check_time - start_check_time > self.trigger_overrun:
                _Logger().warning(
                    f"Command trigger check took too long to complete. {func.__name__}: {(end_check_time - start_check_time) * 1000}ms"
                )

            if current_state and state_changed and trigger.actions.on_true:
                self._schedule(trigger.actions.on_true, trigger)

            if not current_state and state_changed and trigger.actions.on_false:
                self._schedule(trigger.actions.on_false, trigger)

            if (
                current_state
                and trigger.actions.while_true
                and state_changed
                and not any(scheduled["command"] is trigger.actions.while_true for scheduled in self._scheduled)
            ):
                self._schedule(trigger.actions.while_true, trigger)

            if (
                not current_state
                and trigger.actions.while_false
                and state_changed
                and not any(scheduled["command"] is trigger.actions.while_false for scheduled in self._scheduled)
            ):
                self._schedule(trigger.actions.while_false, trigger)

        # Process all scheduled commands
        i = 0
        while i < len(self._scheduled):
            loop_start_time = time.monotonic()

            scheduled = self._scheduled[i]
            command = scheduled["command"]
            trigger = scheduled["trigger"]

            # Initialize command if not already initialized
            if not scheduled["has_init"]:
                command.init()
                scheduled["has_init"] = True

            # Check if trigger conditions are still satisfied for while_* commands
            func = None
            end_check_time, start_check_time = None, None
            if trigger:
                start_check_time = time.monotonic()
                current_state, _, func = trigger.check()
                end_check_time = time.monotonic()

                if end_check_time - start_check_time > self.trigger_overrun:
                    _Logger().warning(
                        f"Command trigger check took too long to complete. {func.__name__}: {(end_check_time - start_check_time) * 1000}ms"
                    )
                is_while_command = (trigger.actions.while_true is command and not current_state) or (
                    trigger.actions.while_false is command and current_state
                )
                if is_while_command:
                    # End and remove the command if trigger conditions are no longer satisfied
                    command.end()
                    self._scheduled.pop(i)
                    continue

            # Execute command
            command.execute()

            # Check if the command is finished
            if command.finished():
                command.end()
                self._scheduled.pop(i)
            else:
                i += 1

            loop_end_time = time.monotonic()
            if loop_end_time - loop_start_time > self.command_overrun:
                _Logger().warning(
                    f"Command execution took too long to complete.\n{command.__class__.__name__}: {(loop_end_time - loop_start_time) * 1000}ms"
                    + (
                        f"\n(includes trigger check time: {func.__name__}: {(end_check_time - start_check_time) * 1000}ms)"
                        if trigger and func
                        else ""
                    )
                )
