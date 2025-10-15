from __future__ import annotations
import inspect
import importlib
from typing import Iterable, Type

try:
    from importlib.metadata import entry_points  # py>=3.10
except Exception:  # pragma: no cover
    from importlib_metadata import entry_points  # type: ignore

BUNDLES_EP_GROUP = "apeex.bundles"


def discover_entrypoint_bundles() -> list[Type]:
    eps = entry_points()
    group = eps.select(group=BUNDLES_EP_GROUP) if hasattr(eps, "select") else eps.get(BUNDLES_EP_GROUP, [])
    classes: list[Type] = []
    for ep in group:
        try:
            cls = ep.load()
        except (ImportError, ModuleNotFoundError, AttributeError, ValueError) as _e:
            # Skip broken entry points (can add logging here if needed)
            continue
        if inspect.isclass(cls):
            classes.append(cls)
    return classes


def discover_local_bundles() -> list[Type]:
    """Best-effort локальный поиск бандлов в пространстве apeex.bundles.*"""
    classes: list[Type] = []
    # Попробуем импортировать известные корни; расширяйте по необходимости
    guesses = (
        "apeex.bundles.demo_bundle",
        "apeex.bundles.app_bundle",
    )
    for guess in guesses:
        try:
            mod = importlib.import_module(guess)
            classes.extend(_extract_bundle_classes(mod))
        except Exception:
            pass
    # Уникальность
    unique: dict[Type, None] = {}
    for c in classes:
        unique[c] = None
    return list(unique.keys())


def _extract_bundle_classes(module) -> list[Type]:
    from apeex.bundles.bundle import Bundle
    out = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Bundle) and obj is not Bundle:
            out.append(obj)
    return out


