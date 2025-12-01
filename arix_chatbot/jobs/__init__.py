from pathlib import Path
from glob import glob
import importlib
import inspect
import os
from types import new_class
from typing import Literal, TypedDict, List, Union


JOB_REGISTRY = {}
# TYPED_DICTS = {}
EXCLUDE_TASKS = ["__init__.py", "job_ids.py"]
BASE_PATH = Path(__file__).parent


def snake_to_camel(snake):
    return ''.join(word.capitalize() for word in snake.split('_'))


def load_task_classes():
    for filepath in glob((BASE_PATH / "*.py").as_posix()):
        filename = os.path.basename(filepath)
        if filename in EXCLUDE_TASKS:
            continue

        module_name = filename[:-3]  # strip .py
        full_module = f"{__package__}.{module_name}"

        try:
            module = importlib.import_module(full_module)
        except ImportError as e:
            print(f"Could not import module {full_module}: {e}")
            continue

        # Iterate over all classes defined in this module
        for name, cls in inspect.getmembers(module, inspect.isclass):
            # Only classes *defined in this module* (not imported from elsewhere)
            if cls.__module__ != module.__name__:
                continue

            # Only subclasses of Job, and not the base Job itself
            # if not issubclass(cls, Job) or cls is Job:
            #     continue

            # Register by job_type (assuming each subclass defines job_type)
            try:
                job_type = cls.job_type
            except AttributeError:
                print(f"Class {cls.__name__} in {full_module} has no 'job_type'; skipping")
                continue

            if job_type in JOB_REGISTRY:
                print(f"Duplicate job_type {job_type!r} (existing: {JOB_REGISTRY[job_type]}, new: {cls}); skipping new one")
                continue

            if inspect.isclass(cls):
                JOB_REGISTRY[cls.job_type] = cls

# def load_task_classes():
#     for filepath in glob((BASE_PATH / "*.py").as_posix()):
#         filename = os.path.basename(filepath)
#         if filename in EXCLUDE_TASKS:
#             continue
#
#         module_name = filename[:-3]
#         class_name = snake_to_camel(module_name)
#         full_module = f"{__package__}.{module_name}"  # <---- FIXED
#
#         try:
#             module = importlib.import_module(full_module)
#             cls = getattr(module, class_name)
#             if inspect.isclass(cls):
#                 JOB_REGISTRY[cls.job_type] = cls
#         except (ImportError, AttributeError) as e:
#             print(f"Could not import {class_name} from {full_module}: {e}")


def get_class_init_args(cls):
    """
    Return a dictionary with parameter names and default values for a given class's __init__ method.
    Excludes 'self', 'name', 'description' (handled separately).
    """
    sig = inspect.signature(cls.__init__)
    args = {}
    for name, param in sig.parameters.items():
        if name in {"self", "name", "description"}:
            continue
        if param.default is not inspect.Parameter.empty:
            args[name] = param.default
        else:
            args[name] = None  # No default, mark as required
    return args


def get_class_init_args(cls):
    sig = inspect.signature(cls.__init__)
    args = {}
    for name, param in sig.parameters.items():
        if name in {"self", "name", "description"}:
            continue
        if param.annotation is not inspect._empty:
            args[name] = param.annotation
        else:
            args[name] = str  # Fallback
    return args


def create_typed_dict_class(class_name: str, task_type: str, kwargs_fields: dict):
    kwargs_name = f"{class_name}Kwargs"

    # Step 1: Create inner kwargs TypedDict
    def kwargs_body(ns):
        ns['__annotations__'] = kwargs_fields

    kwargs_class = new_class(kwargs_name, (TypedDict,), exec_body=kwargs_body)

    # Step 2: Create outer task config TypedDict
    def outer_body(ns):
        ns['__annotations__'] = {
            "type": Literal[task_type],
            "name": str,
            "description": str,
            "kwargs": kwargs_class,
        }

    outer_class = new_class(class_name, (TypedDict,), exec_body=outer_body)
    return outer_class


# Load tasks and generate TypedDicts
load_task_classes()
pass
