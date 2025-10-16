import traceback
import functools
import logging


depreclog = logging.getLogger("nxtomomill.DEPRECATION")

deprecache = set([])


def deprecated_warning(
    type_,
    name,
    reason=None,
    replacement=None,
    since_version=None,
    only_once=True,
    skip_backtrace_count=0,
):
    """
    Function to log a deprecation warning

    :param type_: Nature of the object to be deprecated:
        "Module", "Function", "Class" ...
    :param name: Object name.
    :param reason: Reason for deprecating this function
        (e.g. "feature no longer provided",
    :param replacement: Name of replacement function (if the reason for
        deprecating was to rename the function)
    :param since_version: First *silx* version for which the function was
        deprecated (e.g. "0.5.0").
    :param only_once: If true, the deprecation warning will only be
        generated one time for each different call locations. Default is true.
    :param skip_backtrace_count: Amount of last backtrace to ignore when
        logging the backtrace
    """
    if not depreclog.isEnabledFor(logging.WARNING):
        # Avoid computation when it is not logged
        return

    msg = "%s %s is deprecated"
    if since_version is not None:
        msg += " since nxtomomill version %s" % since_version
    msg += "."
    if reason is not None:
        msg += " Reason: %s." % reason
    if replacement is not None:
        msg += " Use '%s' instead." % replacement
    msg += "\n%s"
    limit = 2 + skip_backtrace_count
    backtrace = "".join(traceback.format_stack(limit=limit)[0])
    backtrace = backtrace.rstrip()
    if only_once:
        data = (msg, type_, name, backtrace)
        if data in deprecache:
            return
        else:
            deprecache.add(data)
    depreclog.warning(msg, type_, name, backtrace)


def deprecated(
    func=None,
    reason=None,
    replacement=None,
    since_version=None,
    only_once=True,
    skip_backtrace_count=1,
):
    """
    Decorator that deprecates the use of a function

    :param reason: Reason for deprecating this function
        (e.g. "feature no longer provided",
    :param replacement: Name of replacement function (if the reason for
        deprecating was to rename the function)
    :param since_version: First *silx* version for which the function was
        deprecated (e.g. "0.5.0").
    :param only_once: If true, the deprecation warning will only be
        generated one time. Default is true.
    :param skip_backtrace_count: Amount of last backtrace to ignore when
        logging the backtrace
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            deprecated_warning(
                type_="Function",
                name=func.__name__,
                reason=reason,
                replacement=replacement,
                since_version=since_version,
                only_once=only_once,
                skip_backtrace_count=skip_backtrace_count,
            )
            return func(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
