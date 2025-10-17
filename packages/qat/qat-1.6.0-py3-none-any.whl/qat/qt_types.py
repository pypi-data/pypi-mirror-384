# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Module providing wrapper classes for Qt types (e.g. QColor, QPoint,...)
"""

# pylint: disable = too-few-public-methods
# pylint: disable = too-many-arguments

from array import array
from enum import IntEnum
import inspect
from qat.internal.qt_custom_object import QtCustomObject

class QColor(QtCustomObject):
    """
    QtCustomObject specialization for the QColor type.
    """
    def __init__(
            self,
            name: str = None, *,
            red: int = None,
            green: int = None,
            blue: int = None,
            alpha: int = None,
            ) -> None :
        """
        Create a color with the given parameters.
        The name can be any supported Qt name or ARGB hexadecimal value.
        If 'alpha' is not set, it will be set to 255 (opaque).
        Note: If a name is given, other arguments will be ignored.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QColor'
        if isinstance(name, str):
            attributes['name'] = name

        if isinstance(alpha, int):
            attributes['alpha'] = alpha

        if isinstance(red, int) and isinstance(green, int) and isinstance(green, int):
            attributes['red'] = red
            attributes['green'] = green
            attributes['blue'] = blue
            if isinstance(name, str):
                print("Warning: QColor: RGB values will be ignored since a color name was given")
        super().__init__(attributes)


class QBrush(QtCustomObject):
    """
    QtCustomObject specialization for the QBrush type.
    """

    # pylint: disable = invalid-name
    class BrushStyle(IntEnum):
        """
        Custom definition for Qt::BrushStyle enum
        """
        NoBrush=0
        SolidPattern=1
        Dense1Pattern=2
        Dense2Pattern=3
        Dense3Pattern=4
        Dense4Pattern=5
        Dense5Pattern=6
        Dense6Pattern=7
        Dense7Pattern=8
        HorPattern=9
        VerPattern=10
        CrossPattern=11
        BDiagPattern=12
        FDiagPattern=13
        DiagCrossPattern=14
        LinearGradientPattern=15
        ConicalGradientPattern=16
        RadialGradientPattern=17
        TexturePattern=18

    def __init__(
            self,
            color: QColor = None, *,
            style: BrushStyle = None,
            ) -> None :
        """
        Create a brush based on the given color and style.
        If an argument is missing, a default value will be used (black, SolidPattern).
        Note: gradients are not supported.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QBrush'
        if isinstance(color, QColor):
            attributes['color'] = color

        if isinstance(style, (QBrush.BrushStyle, int)):
            attributes['style'] = style
        super().__init__(attributes)


class QFont(QtCustomObject):
    """
    QtCustomObject specialization for the QFont type.
    """

    # pylint: disable = invalid-name
    class Weight(IntEnum):
        """
        Custom definition for QFont::Weight enum
        """
        Thin=0
        ExtraLight=1
        Light=2
        Normal=3
        Medium=4
        DemiBold=5
        Bold=6
        ExtraBold=7
        Black=8

    # pylint: disable = unused-argument
    def __init__(
            self,
            family: str = None, *,
            bold: bool = None,
            italic: bool = None,
            strikeOut: bool = None,
            underline: bool = None,
            fixedPitch: bool = None,
            pixelSize: int = None,
            pointSize: int = None,
            weight: Weight = None,
            ) -> None :
        """
        Create a font with the given parameters.
        If an argument is missing, the default value will be used.
        Note: 'pixelSize' and 'pointSize' cannot be both set.
        Note: 'weight' takes precedence over 'bold'.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QFont'

        if bold is not None and weight is not None:
            print("Warning: QFont: 'bold' and 'weight' may be conflicting")
        if pixelSize is not None and pointSize is not None:
            print("Warning: QFont: 'pixelSize' and 'pointSize' cannot be both set. Using 'pointSize only'.")

        if isinstance(family, str):
            attributes['family'] = family

        sig = inspect.signature(self.__init__)
        for k,v in sig.parameters.items():
            if v.kind is inspect.Parameter.KEYWORD_ONLY:
                value = locals()[k]
                if value is not None:
                    attributes[k] = value

        super().__init__(attributes)


class QPoint(QtCustomObject):
    """
    QtCustomObject specialization for the QPoint type.
    """
    def __init__(
            self,
            x: int = 0,
            y: int = 0
            ) -> None :
        """
        Create a point with the given coordinates.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QPoint'
        attributes['x'] = int(x)
        attributes['y'] = int(y)
        super().__init__(attributes)


class QPointF(QtCustomObject):
    """
    QtCustomObject specialization for the QPointF type.
    """
    def __init__(
            self,
            x: float = 0.0,
            y: float = 0.0
            ) -> None :
        """
        Create a point with the given coordinates.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QPointF'
        attributes['x'] = float(x)
        attributes['y'] = float(y)
        super().__init__(attributes)


class QLine(QtCustomObject):
    """
    QtCustomObject specialization for the QLine type.
    """
    def __init__(
            self,
            p1: QPoint = QPoint(),
            p2: QPoint = QPoint()
            ) -> None :
        """
        Create a line between the two given points.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QLine'
        attributes['p1'] = p1
        attributes['p2'] = p2
        super().__init__(attributes)


    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, (QLine, QtCustomObject)):
            return self.type == other.type and \
                   self.__dict__['_attributes']['p1'] == other.__dict__['_attributes']['p1'] and \
                   self.__dict__['_attributes']['p2'] == other.__dict__['_attributes']['p2']
        return False


class QLineF(QtCustomObject):
    """
    QtCustomObject specialization for the QLineF type.
    """
    def __init__(
            self,
            p1: QPointF = QPointF(),
            p2: QPointF = QPointF()
            ) -> None :
        """
        Create a line between the two given points.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QLineF'
        attributes['p1'] = p1
        attributes['p2'] = p2
        super().__init__(attributes)


class QSize(QtCustomObject):
    """
    QtCustomObject specialization for the QSize type.
    """
    def __init__(
            self,
            width: int = 0,
            height: int = 0
            ) -> None :
        """
        Create a size with the given width and height.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QSize'
        attributes['width'] = int(width)
        attributes['height'] = int(height)

        super().__init__(attributes)


class QSizeF(QtCustomObject):
    """
    QtCustomObject specialization for the QSize type.
    """
    def __init__(
            self,
            width: float = 0.0,
            height: float = 0.0
            ) -> None :
        """
        Create a size with the given width and height.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QSizeF'
        attributes['width'] = float(width)
        attributes['height'] = float(height)

        super().__init__(attributes)


class QRect(QtCustomObject):
    """
    QtCustomObject specialization for the QRect type.
    """
    def __init__(
            self,
            origin: QPoint = QPoint(0, 0),
            size: QSize = QSize(0,0)
            ) -> None :
        """
        Create a rectangle with the given origin (top-left corner) and size.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QRect'
        attributes['x'] = origin.x
        attributes['y'] = origin.y
        attributes['width'] = size.width
        attributes['height'] = size.height
        super().__init__(attributes)


class QRectF(QtCustomObject):
    """
    QtCustomObject specialization for the QRectF type.
    """
    def __init__(
            self,
            origin: QPointF = QPointF(0, 0),
            size: QSizeF = QSizeF(0,0)
            ) -> None :
        """
        Create a rectangle with the given origin and size.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QRectF'
        attributes['x'] = origin.x
        attributes['y'] = origin.y
        attributes['width'] = size.width
        attributes['height'] = size.height
        super().__init__(attributes)


class QVector2D(QtCustomObject):
    """
    QtCustomObject specialization for the QVector2D type.
    """
    def __init__(
            self,
            x: float = 0.0,
            y: float = 0.0
            ) -> None :
        """
        Create a 2D vector with the given coordinates.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QVector2D'
        attributes['x'] = x
        attributes['y'] = y
        super().__init__(attributes)


class QVector3D(QtCustomObject):
    """
    QtCustomObject specialization for the QVector3D type.
    """
    def __init__(
            self,
            x: float = 0.0,
            y: float = 0.0,
            z: float = 0.0
            ) -> None :
        """
        Create a 3D vector with the given coordinates.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QVector3D'
        attributes['x'] = x
        attributes['y'] = y
        attributes['z'] = z
        super().__init__(attributes)


class QVector4D(QtCustomObject):
    """
    QtCustomObject specialization for the QVector4D type.
    """
    def __init__(
            self,
            x: float = 0.0,
            y: float = 0.0,
            z: float = 0.0,
            w: float = 0.0
            ) -> None :
        """
        Create a 4D vector with the given coordinates.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QVector4D'
        attributes['x'] = x
        attributes['y'] = y
        attributes['z'] = z
        attributes['w'] = w
        super().__init__(attributes)


class QQuaternion(QtCustomObject):
    """
    QtCustomObject specialization for the QQuaternion type.
    """
    def __init__(
            self,
            vector: QVector3D = QVector3D(),
            scalar: float = 1.0
            ) -> None :
        """
        Create a quaternion with the given vector and scalar.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QQuaternion'
        attributes['x'] = vector.x
        attributes['y'] = vector.y
        attributes['z'] = vector.z
        attributes['scalar'] = float(scalar)
        super().__init__(attributes)


class QByteArray(QtCustomObject):
    """
    QtCustomObject specialization for the QByteArray type.
    """
    def __init__(
            self,
            byte_array = array('b')
            ) -> None :
        """
        Create a Qt byte array from the given array.
        """
        attributes = {}
        attributes['QVariantTypeName'] = 'QByteArray'
        attributes['bytes'] = byte_array
        super().__init__(attributes)
