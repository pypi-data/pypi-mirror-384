# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Class for the application preferences
"""

import json
import os
from pathlib import Path


class DictDotNotation(dict):
    """dot.notation access to dictionary attributes"""
    def __getattr__(self, name):
        # Automatically extends the dot notation of the preferences
        if self.get(name, None) is None:
            self[name] = self.__class__()
        return self.get(name, None)


    def __setattr__(self, name, value):
        if isinstance(value, dict):
            self[name] = DictDotNotation(value)
        else:
            self[name] = value


    def __delattr__(self, name):
        del self[name]


class DictDotNotationReadOnly(dict):
    """
    dot.notation access to dictionary attributes
    Setter and Deleter are restricted and will raise an Exception when used
    """
    def __getattr__(self, name):
        attr = self.get(name, None)
        if attr is None:
            raise AttributeError(f"Could not access the preference {name}")
        return attr


    def __setattr__(self, name, value):
        raise AttributeError(f"Updating the preference {name} is not possible in read-only")


    def __delattr__(self, name):
        raise AttributeError(f"Deleting the preference {name} is not possible in read-only")


class Preferences():
    """
    Class implementing the application preferences access (read/write/delete) and read only in RAII
    Note: When not in read only:
      - The preferences file will be created when preferences are not empty.
      - The preferences file is removed if the preferences are empty.
    """
    def __init__(self, preference_file_path: Path, is_read_only: bool = True) -> None:
        self._preference_file_path = preference_file_path
        self._is_read_only = is_read_only
        try:
            with open(self._preference_file_path, 'r', encoding='utf-8') as file:
                self.preferences = Preferences.__load(json.load(file), self._is_read_only)
        except FileNotFoundError:
            print(f"Unable to open the file {self._preference_file_path}. An empty preference file will be created.")
            self.preferences = DictDotNotationReadOnly() if self._is_read_only else DictDotNotation()


    def __enter__(self):
        return self.preferences


    def __exit__(self, exc_type, exc_value, traceback):
        os.makedirs(self._preference_file_path.parent, exist_ok=True)
        if not self._is_read_only and len(self.preferences) > 0:
            with open(self._preference_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.to_json(), file, indent=3)
        elif not self._is_read_only and len(self.preferences) == 0 and self._preference_file_path.is_file():
            # Removing the preference file when the preferences are empty
            os.remove(self._preference_file_path)


    def to_json(self):
        """
        Clean the preferences of empty dictionaries and prepare the preferences for JSON serialization.

        Returns:
          The preferences without empty dictionaries.
        """
        def clean_empty_preferences(preferences):
            if isinstance(preferences, dict):
                return {
                    key:
                    value for key, value in ((key, clean_empty_preferences(item)) for key, item in preferences.items())
                    if value != {} }
            return preferences

        return clean_empty_preferences(self.preferences)


    @staticmethod
    def __load(data, is_read_only: bool):
        """
        Load the preferences file.

        Args:
          data: The deserialized JSON data.
          is_read_only: Flag indicating the preferences are read-only or not.

        Returns:
          The preferences accessible with python dot notation
        """
        if isinstance(data, dict):
            # Create a modifiable or read only dictionary
            result = DictDotNotationReadOnly() if is_read_only else DictDotNotation()

            for key, value in data.items():
                result[key] = Preferences.__load(value, is_read_only)
            return result

        if isinstance(data, list):
            result = [Preferences.__load(item, is_read_only) for item in data]
            return result

        return data


def get_preferences(read_only: bool = True) -> Preferences:
    """
    Return the user preferences.

    Args:
      read_only: True (default) will prevent preference file from being modified. False will
        synchronize preferences value with the file content.
    """
    preferences_file = Path.home() / '.qat' / 'preferences.json'
    return Preferences(preferences_file, read_only)
