"""
Main Ikomia plugin module.
Ikomia Studio and Ikomia API use it to load algorithms dynamically.
"""
from ikomia import dataprocess
from {{cookiecutter.algo_name}}.{{cookiecutter.algo_name}}_process import (
    {{ cookiecutter.class_name }}Factory,
    {{ cookiecutter.class_name }}ParamFactory,
)


class IkomiaPlugin(dataprocess.CPluginProcessInterface):
    """
    Interface class to integrate the process with Ikomia application.
    Inherits PyDataProcess.CPluginProcessInterface from Ikomia API.
    """
    def __init__(self):
        dataprocess.CPluginProcessInterface.__init__(self)

    def get_process_factory(self):
        """Instantiate process object."""
        return {{ cookiecutter.class_name }}Factory()

    def get_widget_factory(self):
        """Instantiate associated widget object."""
        from {{cookiecutter.algo_name}}.{{cookiecutter.algo_name}}_widget import (
            {{ cookiecutter.class_name }}WidgetFactory,
        )
        return {{ cookiecutter.class_name }}WidgetFactory()

    def get_param_factory(self):
        """Instantiate algorithm parameters object."""
        return {{ cookiecutter.class_name }}ParamFactory()
