# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Generate default test suite from template
"""

from importlib import resources as res
from pathlib import Path

import argparse
import os
import shutil


def create_suite():
    """
    Create a default suite
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('suite_type', nargs='?', default='bdd', choices=['bdd', 'script'], help="'script' or 'bdd' (default)")
    parser.add_argument('--dest', required=False)
    args = parser.parse_args()
    templates_path = res.files('qat') / 'templates'
    if not templates_path.is_dir():
        templates_path = Path(os.getcwd()) / 'templates'
    destination = args.dest or os.getcwd()
    destination = Path(destination)
    os.makedirs(destination, exist_ok=True)

    common_files = ['applications.json', 'testSettings.json']
    for file in common_files:
        if not os.path.exists(destination / file):
            shutil.copyfile(templates_path / file, destination / file)
    if args.suite_type == 'bdd':
        bdd_files=[
            'environment.py',
        ]
        destination = destination / 'features/'
        os.makedirs(destination, exist_ok=True)
        for file in bdd_files:
            if not os.path.exists(destination / file):
                shutil.copyfile(templates_path / file, destination / file)
        bdd_folders=[
            'demo',
            'scripts',
            'steps'
        ]
        for folder in bdd_folders:
            os.makedirs(destination / folder, exist_ok=True)
            shutil.copytree(templates_path / folder, destination / folder, dirs_exist_ok=True)
    else:
        script_files=[
            'demo.py',
            'scripts/object_dictionary.py'
        ]
        os.makedirs(destination / 'scripts', exist_ok=True)
        for file in script_files:
            if not os.path.exists(destination / file):
                shutil.copyfile(templates_path / file, destination / file)


if __name__ == "__main__":
    create_suite()