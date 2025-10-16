from collections.abc import Callable
from functools import wraps
from typing import Any

import click

from exponent.commands.utils import (
    print_editable_install_forced_prod_warning,
    print_editable_install_warning,
)
from exponent.core.config import (
    Environment,
    get_settings,
    is_editable_install,
)


def use_settings(f: Callable[..., Any]) -> Callable[..., Any]:
    @click.option(
        "--prod",
        is_flag=True,
        hidden=True,
        help="Use production URLs even if in editable mode",
    )
    @click.option(
        "--staging",
        is_flag=True,
        hidden=True,
        help="Use staging URLs even if in editable mode",
    )
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        prod = kwargs.pop("prod", False)
        staging = kwargs.pop("staging", False)
        settings = get_settings(use_prod=prod, use_staging=staging)

        if is_editable_install() and not (prod or staging):
            assert settings.environment == Environment.development
            print_editable_install_warning(settings)

        return f(*args, settings=settings, **kwargs)

    return decorated_function


def use_prod_settings(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        settings = get_settings(use_prod=True)

        if is_editable_install():
            print_editable_install_forced_prod_warning(settings)

        return f(*args, settings=settings, **kwargs)

    return decorated_function
