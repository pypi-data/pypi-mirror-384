import random
from functools import partial
from django.utils import timezone
from django.utils.module_loading import import_string

from dateutil.parser import parse as parse_dt

from .conf import get_setting


random_bool = partial(random.choice, [True, False])


def parse_datetime(dtstr):
    dt = parse_dt(dtstr)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)

    return dt


def can_picker_participate():
    hooks = None

    def inner(picker, gs):
        nonlocal hooks
        if hooks is None:
            hooks = [import_string(h) for h in get_setting("PARTICIPATION_HOOKS", [])]
        return all(hook(picker, gs) for hook in hooks) if hooks else True

    return inner


can_picker_participate = can_picker_participate()


def weighted_standings(items):
    weighted = []
    prev_place, prev_results = 1, (0, 0)
    for i, item in enumerate(items, 1):
        results = (item.correct, item.points_delta)
        item.place = prev_place if results == prev_results else i
        prev_place, prev_results = item.place, results
        weighted.append(item)

    return weighted


def get_templates(component, league=None):
    if component.startswith("@"):
        dirs = [component.replace("@", "picker/{}/".format(league.slug))] if league else []
        dirs.extend(
            [
                component.replace("@", "picker/"),
                component.replace("@", "picker/_base/"),
            ]
        )
        return dirs

    return component
