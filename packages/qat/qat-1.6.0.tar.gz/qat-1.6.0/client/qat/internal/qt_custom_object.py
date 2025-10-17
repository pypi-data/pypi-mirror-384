# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Provides the QtCustomObject class
"""

from copy import deepcopy


class QtCustomObject():
    """
    Class binding local attributes and methods to a remote Qt object
    """

    def __init__(self, attributes: dict) -> None:
        """
        Store the object's attributes
        """
        self.__dict__['_attributes'] = deepcopy(attributes)
        self.__dict__['typeId'] = None
        self.__dict__['type'] = None
        if 'QVariantType' in self.__dict__['_attributes']:
            self.__dict__['typeId'] = self.__dict__[
                '_attributes']['QVariantType']
            del self.__dict__['_attributes']['QVariantType']
        if 'QVariantTypeName' in self.__dict__['_attributes']:
            self.__dict__['type'] = self.__dict__[
                '_attributes']['QVariantTypeName']
            del self.__dict__['_attributes']['QVariantTypeName']
        # Handle nested objects
        for att in attributes:
            if isinstance(attributes[att], dict):
                self.__dict__['_attributes'][att] = QtCustomObject(attributes[att])
            elif isinstance(attributes[att], QtCustomObject):
                self.__dict__['_attributes'][att] = attributes[att]


    def get_attribute_dict(self) -> dict:
        """
        Return the object's attributes
        """
        all_attributes = deepcopy(self.__dict__['_attributes'])
        if self.typeId is not None:
            all_attributes['QVariantType'] = self.__dict__['typeId']
        if self.type is not None:
            all_attributes['QVariantTypeName'] = self.__dict__['type']
        # Handle nested objects
        for att in self.__dict__['_attributes']:
            if isinstance(self.__dict__['_attributes'][att], QtCustomObject):
                all_attributes[att] = self.__dict__['_attributes'][att].get_attribute_dict()

        return all_attributes


    def __str__(self):
        """
        Custom string representation of a QtCustomObject
        """
        return str(self.__dict__['_attributes'])


    def __getattr__(self, name: str):
        """
        Get an attribute of this object.
        """
        attributes = self.__dict__['_attributes']
        if name not in attributes:
            raise AttributeError(f"Attribute {name} does not exist")

        return attributes[name]


    def __setattr__(self, name: str, value):
        """
        Set a (local) attribute of this object.
        """
        if name == 'typeId':
            self.__dict__['typeId'] = value
            return
        if name == 'type':
            self.__dict__['type'] = value
            return
        attributes = self.__dict__['_attributes']
        if name not in attributes:
            raise AttributeError(f"Attribute {name} does not exist")

        attributes[name] = value


    # Forwarding supported classic operations to underlying value

    def __len__(self):
        return self.__dict__['_attributes'].__len__()


    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, QtCustomObject):
            return self.__dict__['_attributes'] == other.__dict__['_attributes']
        if isinstance(other, dict):
            return self.__dict__['_attributes'] == other
        return False


    def __getitem__(self, key):
        attributes = self.__dict__['_attributes']
        if key in attributes:
            return attributes.__getitem__(key)

        if self.type == 'QColor':
            values = [attributes['red'], attributes['green'],
                      attributes['blue'], attributes['alpha']]
            return values.__getitem__(key)
        return list(attributes.values()).__getitem__(key)


    def __setitem__(self, key, value):
        attributes = self.__dict__['_attributes']
        if key in attributes:
            return attributes.__setitem__(key, value)

        raise AttributeError(f'Setting {key} attribute is not supported')


    def __iter__(self):
        return self.__dict__['_attributes'].__iter__()


    def __contains__(self, item):
        return self.__dict__['_attributes'].__contains__(item)


    def __deepcopy__(self, memo):
        return deepcopy(self.__dict__['_attributes'])
