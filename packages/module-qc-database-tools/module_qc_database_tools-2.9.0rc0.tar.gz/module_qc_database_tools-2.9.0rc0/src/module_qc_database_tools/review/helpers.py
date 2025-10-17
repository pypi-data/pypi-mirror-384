from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable

from module_qc_database_tools.exceptions import SkipCheck
from module_qc_database_tools.typing_compat import (
    CheckFunction,
    CheckResult,
    Dict,
    Tuple,
)


class Check:
    """
    Check class for checking groups of tests by orchestrating the execution of those checks and utilities for wrapping check failures accordingly

    When you create an instance of this, it is typically used as a decorator on a function that should be used for checking statusing.

    This wraps the function so that when it is called later:

    - returns a two-tuple of `(status, message)`
    - is a singleton (only called once), and returns nothing if already called before

    | `status`    | `message`    | Description                                  |
    | ----------- | ------------ | -------------------------------------------- |
    | `True`      | `"Ok"`       | :material-check:             Check Passed    |
    | `False`     | `"<reason>"` | :material-close:             Check Failed    |
    | `None`      | `"<reason>"` | :octicons-skip-24:           Check Skipped   |
    | `None`      | `None`       | :material-content-duplicate: Check Duplicate |

    For situations where the `message` is a string (such as failing or skipping a check), the reason for such a scenario will be the `message` value.

    **Example:**

    ```pycon
    >>> from module_qc_database_tools.review.helpers import Check, skipif
    >>> checker = Check(allowed_params={"value"})
    >>> @checker
    ... @skipif("value", lambda x: x == "skip", "The value is 'skip'")
    ... def check_this(value):
    ...     assert value, "The value is not True"
    ...
    >>>
    >>> check_this(value=True)  # (1)!
    (True, 'Ok')
    >>> check_this(value=False)  # (2)!
    (False, 'The value is not True')
    >>> check_this(value=True)  # (3)!
    (None, None)
    >>> check_this(value=False)  # (3)!
    (None, None)
    >>> check_this(value="skip")  # (4)!
    (None, "Skipping check_this for value = skip: The value is 'skip'")
    >>> check_this(value="skip")  # (5)!
    (None, None)
    ```

    1. This check is ok.
    2. This check failed.
    3. This check was skipped because it's been called already.
    4. This check was skipped explicitly because of it's value.
    5. This check was skipped because it's been called already.
    """

    _checks: Dict[str, CheckFunction]
    executed_checks: set[Tuple[str, Tuple[Tuple[str, Any]]]]
    allowed_params: set[str]

    def __init__(self, *, allowed_params):
        """
        Instantiate a Check checker for running and calling various checks.
        """
        self._checks = {}
        self.executed_checks = set()
        self.allowed_params = allowed_params

    def __call__(self, func: CheckFunction) -> CheckFunction:
        """
        The decorator to create a new check.
        """

        if func.__name__ in self._checks:
            msg = f"Overwriting existing check {func.__name__}."
            raise ValueError(msg)

        signature = inspect.signature(func)
        param_names = set(signature.parameters.keys())
        # Find parameters that are not allowed
        invalid_params = param_names - self.allowed_params
        if invalid_params:
            msg = f"{func.__name__}() has an unexpected keyword argument: {invalid_params}"
            raise TypeError(msg)

        @wraps(func)
        def wrapper(*args, **kwargs) -> Tuple[bool | None, str | None]:
            """
            Call a check and obtain status.

            If a check passes, returns True.
            If a check fails, returns the exception.
            If a check is skipped, returns None.
            """
            check_key = (func.__name__, tuple(sorted(kwargs.items())))

            # duplicate
            if check_key in self.executed_checks:
                return None, None
            self.executed_checks.add(check_key)

            try:
                func(*args, **kwargs)
                return True, "Ok"
            except SkipCheck as exc:
                return None, str(exc)
            except AssertionError as exc:
                return False, str(exc) or "no reason given"
            except Exception as exc:  # pylint: disable=broad-exception-caught
                return False, f"{type(exc).__name__}: {exc}"

        self._checks[func.__name__] = wrapper
        return wrapper

    @property
    def checks(self) -> Dict[str, CheckFunction]:
        """
        Dictionary of checks to execute.
        """
        return dict(sorted(self._checks.items()))

    def run_checks(
        self, filter_checks: str = "", **fixtures: Any
    ) -> Dict[str, CheckResult]:
        """
        Run all checks using the provided fixtures as values injected into the check.

        This will go through all defined checks, determine if the check can be called with the provided fixtures, and then call the check and handle the results of calling the check.

        **Example:**

        ```pycon
        >>> from module_qc_database_tools.review.helpers import Check
        >>> checker = Check(allowed_params={"value"})
        >>> @checker
        ... def check_this(value):
        ...     assert value, "The value is not True"
        ...
        >>> checker.run_checks()  # (1)!
        {}
        >>> checker.run_checks(value=True)  # (2)!
        {'check_this': {'args': (True,), 'status': True, 'message': 'Ok'}}
        >>> Check.run_checks(value=False)  # (3)!
        {'check_this': {'args': (False,), 'status': False, 'message': 'The value is not True'}}
        ```

        1. No checks ran, because there were no checks to run for the empty set of fixtures provided.
        2. The `check_this` check ran successfully with no errors.
        3. The `check_this` check failed to assert with a message of `"The value is not True"`

        Args:
            filter_checks: run only checks containing this substring
            fixtures: key-value pairs matching the [allowed_params][module_qc_database_tools.review.helpers.Check.allowed_params] for all checks

        Returns:
            results: dictionary of results for each function that was able to be called with the set of fixtures provided.

        """
        invalid_params = set(fixtures.keys()) - self.allowed_params
        if invalid_params:
            msg = f"run_checks() got an unexpected keyword argument: {invalid_params}"
            raise TypeError(msg)

        results = {}
        for name, check in self.checks.items():
            if filter_checks and filter_checks not in name:
                continue

            signature = inspect.signature(check)
            required_params = set(signature.parameters.keys())
            # Ensure all required parameters are present
            if not required_params.issubset(fixtures.keys()):
                continue

            # skip checks that need both top_component and component, as they should just be different
            if {"top_component", "component"}.issubset(required_params) and fixtures[
                "top_component"
            ] == fixtures["component"]:
                continue
            # Build the arguments to pass to the underlying check
            args = [(param, fixtures[param]) for param in required_params]
            status, message = check(**dict(args))
            # Skipped either because Duplicate or SkipCheck(reason)
            if status is None and message is None:
                continue

            results[name] = {
                "args": tuple(param[1] for param in args),
                "status": status,
                "message": message,
            }

        return results


def conditional_skipper(
    arg_name: str,
    condition: Callable[[Any], bool],
    reason: str | None,
    negate: bool = False,
) -> Callable[CheckFunction, bool]:
    """
    Generic function for providing conditional skipping of a check. This is treated as a decorator.

    Args:
        arg_name: the argument to apply condition on
        condition: callable that evaluates the provided argument and returns a boolean
        reason: the reason for skipping the check
        negate: the value of the condition that should not be skipped (e.g. negate=`False` means a truthy condition will trigger a skip)

    Returns:
        decorator: returns a callable function that wraps everything

    Example:

        from module_qc_database_tools.review.helpers import Check
        checker = Check()

        @checker
        @conditional_skipper('component', lambda x: component.component_type == 'MODULE_CARRIER', negate=False)
        def check_component_type(component):
            assert component.component_type != "MODULE_CARRIER", "This component is a module carrier"

    """

    def decorator(func: CheckFunction) -> Callable[..., bool]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> bool:
            signature = inspect.signature(func)
            if arg_name not in signature.parameters:
                msg = f"conditional_skipper() got an unexpected keyword argument for {func.__name__}: {arg_name}"
                raise TypeError(msg)

            bound_args = signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            obj = bound_args.arguments[arg_name]
            if condition(obj) != negate:
                msg = f"Skipping {func.__name__} for {arg_name} = {obj}"
                if reason:
                    msg = f"{msg}: {reason}"
                raise SkipCheck(msg)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def skipif(arg_name: str, condition: Callable[..., bool], reason: str | None = None):
    """
    Skip a check if the given argument passes the condition. See [conditional_skipper][module_qc_database_tools.review.helpers.conditional_skipper] for more information.

    Example:

        from module_qc_database_tools.review.helpers import Check
        checker = Check()

        @checker
        @skipif('component', lambda x: component.component_type == 'MODULE_CARRIER')
        def check_component_type(component):
            assert component.component_type != "MODULE_CARRIER", "This component is a module carrier"
    """
    return conditional_skipper(arg_name, condition, reason=reason, negate=False)


def onlyif(arg_name: str, condition: Callable[..., bool], reason: str | None = None):
    """
    Skip a check unless the given argument passes the condition. See [conditional_skipper][module_qc_database_tools.review.helpers.conditional_skipper] for more information.

    Example:

        from module_qc_database_tools.review.helpers import Check
        checker = Check()

        @checker
        @onlyif('component', lambda x: component.component_type == 'MODULE_CARRIER')
        def check_component_type(component):
            assert component.component_type == "MODULE_CARRIER", "This component is not a module carrier"

    """
    return conditional_skipper(arg_name, condition, reason=reason, negate=True)
