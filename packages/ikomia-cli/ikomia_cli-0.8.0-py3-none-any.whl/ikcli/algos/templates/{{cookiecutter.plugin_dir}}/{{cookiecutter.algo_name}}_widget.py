"""
Module that implements the UI widget of the algorithm.
"""
{%- if cookiecutter.widget_class == "CWorkflowTaskWidget" %}
{%-   set widget_class_fqdn = "core.CWorkflowTaskWidget" %}
{%- else %}
{%-   set widget_class_fqdn = "dataprocess." + cookiecutter.widget_class %}
{%- endif %}
from ikomia import core, dataprocess
from ikomia.utils import pyqtutils, qtconversion
from {{cookiecutter.algo_name}}.{{cookiecutter.algo_name}}_process import (
    {{ cookiecutter.class_name }}Param,
)

{%- if cookiecutter.qt_framework == "pyqt" %}
from PyQt5.QtWidgets import *

{%- else %}
from PySide2 import QtCore, QtGui, QtWidgets

{%- endif %}


class {{ cookiecutter.class_name }}Widget({{ widget_class_fqdn }}):
    """
    Class that implements UI widget to adjust algorithm parameters.
    Inherits PyCore.CWorkflowTaskWidget from Ikomia API.
    """
    def __init__(self, param, parent):
        {{ widget_class_fqdn }}.__init__(self, parent)

        if param is None:
            self.parameters = {{ cookiecutter.class_name }}Param()
        else:
            self.parameters = param

{%- if cookiecutter.qt_framework == "pyqt" %}

        # Create layout : QGridLayout by default
        self.grid_layout = QGridLayout()
        # PyQt -> Qt wrapping
        layout_ptr = qtconversion.PyQtToQt(self.grid_layout)

{%- else %}

        # Create layout : QGridLayout by default
        self.grid_layout = QtWidgets.QGridLayout()
        # PySide -> Qt wrapping
        layout_ptr = qtconversion.PySideToQt(self.grid_layout)

{%- endif %}

        # Set widget layout
        self.set_layout(layout_ptr)

    def on_apply(self):
        """QT slot called when users click the Apply button."""
        # Get parameters from widget
        # Example : self.parameters.windowSize = self.spinWindowSize.value()

        # Send signal to launch the process
        self.emit_apply(self.parameters)


class {{ cookiecutter.class_name }}WidgetFactory(dataprocess.CWidgetFactory):
    """
    Factory class to create algorithm widget object.
    Inherits PyDataProcess.CWidgetFactory from Ikomia API.
    """
    def __init__(self):
        dataprocess.CWidgetFactory.__init__(self)
        # Set the name of the process -> it must be the same as the one declared in the process factory class
        self.name = "{{ cookiecutter.algo_name }}"

    def create(self, param):
        """Instantiate widget object."""
        return {{ cookiecutter.class_name }}Widget(param, None)
