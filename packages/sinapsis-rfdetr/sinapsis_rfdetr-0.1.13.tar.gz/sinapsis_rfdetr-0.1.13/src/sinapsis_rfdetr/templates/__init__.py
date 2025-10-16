# -*- coding: utf-8 -*-
import importlib
from typing import Any, Callable, cast

_root_lib_path = "sinapsis_rfdetr.templates"

_template_lookup = {
    "RFDETRExport": f"{_root_lib_path}.rfdetr_export",
    "RFDETRLargeExport": f"{_root_lib_path}.rfdetr_export",
    "RFDETRInference": f"{_root_lib_path}.rfdetr_inference",
    "RFDETRLargeInference": f"{_root_lib_path}.rfdetr_inference",
    "RFDETRTrain": f"{_root_lib_path}.rfdetr_train",
    "RFDETRLargeTrain": f"{_root_lib_path}.rfdetr_train",
}


def __getattr__(name: str) -> Callable[..., Any]:
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        attr = getattr(module, name)
        if callable(attr):
            return cast(Callable[..., Any], attr)
        raise TypeError(f"Attribute `{name}` in `{_template_lookup[name]}` is not callable.")

    raise AttributeError(f"template `{name}` not found in {_root_lib_path}")


__all__ = list(_template_lookup.keys())
