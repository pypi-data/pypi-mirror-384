"""
Module that implements the core logic of algorithm execution.
"""
{%- if cookiecutter.base_class == "CWorkflowTask" %}
{%-   set base_class_fqdn = "core.CWorkflowTask" %}
{%- else %}
{%-   set base_class_fqdn = "dataprocess." + cookiecutter.base_class %}
{%- endif %}
import copy

from ikomia import core, dataprocess


class {{ cookiecutter.class_name }}Param(core.CWorkflowTaskParam):
    """
    Class to handle the algorithm parameters.
    Inherits PyCore.CWorkflowTaskParam from Ikomia API.
    """
    def __init__(self):
        core.CWorkflowTaskParam.__init__(self)
        # Place default value initialization here
        # Example : self.windowSize = 25

    def set_values(self, params):
        """
        Set parameters values from Ikomia Studio or API.
        Parameters values are stored as string and accessible like a python dict.
        Example : self.window_size = int(params["window_size"])
        """
        pass

    def get_values(self):
        """
        Send parameters values to Ikomia Studio or API.
        Create the specific dict structure (key-value as string).
        """
        params = {}
        # Example : params["windowSize"] = str(self.windowSize)
        return params


class {{ cookiecutter.class_name }}ParamFactory(dataprocess.CTaskParamFactory):
    """Factory class to create parameters object."""
    def __init__(self):
        dataprocess.CTaskParamFactory.__init__(self)
        self.name = "{{ cookiecutter.algo_name }}"

    def create(self):
        """Instantiate parameters object."""
        return {{ cookiecutter.class_name }}Param()


class {{ cookiecutter.class_name }}({{ base_class_fqdn }}):
    """
    Class that implements the algorithm.
    Inherits PyCore.CWorkflowTask or derived from Ikomia API.
    """
    def __init__(self, name, param):
        {{ base_class_fqdn }}.__init__(self, name)
        # Add input/output of the process here
        # Example :  self.add_input(dataprocess.CImageIO())
        #           self.add_output(dataprocess.CImageIO())

        # Create parameters class
        if param is None:
            self.set_param_object({{ cookiecutter.class_name }}Param())
        else:
            self.set_param_object(copy.deepcopy(param))

    def get_progress_steps(self):
        """
        Ikomia Studio only.
        Function returning the number of progress steps for this algorithm.
        This is handled by the main progress bar of Ikomia Studio.
        """
        return 1

    def run(self):
        """Main function and entry point for algorithm execution."""
        # Call begin_task_run() for initialization
        self.begin_task_run()

        # Examples :
        # Get input :
        # task_input = self.get_input(index_of_input)

        # Get output :
        # task_output = self.get_output(index_of_output)

        # Get parameters :
        # param = self.get_param_object()

        # Get image from input/output (numpy array):
        # src_image = task_input.get_image()

        # Call to the process main routine
        # dst_image = ...

        # Set image of input/output (numpy array):
        # task_output.set_image(dst_image)

        # Step progress bar:
        self.emit_step_progress()

        # Call end_task_run() to finalize process
        self.end_task_run()


class {{ cookiecutter.class_name }}Factory(dataprocess.CTaskFactory):
    """
    Factory class to create process object.
    Inherits PyDataProcess.CTaskFactory from Ikomia API.
    """
    def __init__(self):
        dataprocess.CTaskFactory.__init__(self)
        # Set process information as string here
        self.info.name = "{{ cookiecutter.algo_name }}"
        self.info.short_description = "your short description"
        # relative path -> as displayed in Ikomia Studio process tree
        self.info.path = "Plugins/Python"
        self.info.version = "1.0.0"
        # self.info.icon_path = "your path to a specific icon"
        self.info.authors = "algorithm author"
        self.info.article = "title of associated research article"
        self.info.article_url = ""
        self.info.journal = "publication journal"
        self.info.year = 2024
        self.info.license = ""

        # Ikomia API compatibility
        # self.info.min_ikomia_version = "0.10.0"
        # self.info.max_ikomia_version = "0.11.0"

        # Python compatibility
        # self.info.min_python_version = "3.10.0"
        # self.info.max_python_version = "3.11.0"

        # URL of documentation
        self.info.documentation_link = ""

        # Code source repository
        self.info.repository = ""
        self.info.original_repository = ""

        # Keywords used for search
        self.info.keywords = "your,keywords,here"

        # General type: INFER, TRAIN, DATASET or OTHER
        # self.info.algo_type = core.AlgoType.OTHER

        # Algorithms tasks: CLASSIFICATION, COLORIZATION, IMAGE_CAPTIONING, IMAGE_GENERATION,
        # IMAGE_MATTING, INPAINTING, INSTANCE_SEGMENTATION, KEYPOINTS_DETECTION,
        # OBJECT_DETECTION, OBJECT_TRACKING, OCR, OPTICAL_FLOW, OTHER, PANOPTIC_SEGMENTATION,
        # SEMANTIC_SEGMENTATION or SUPER_RESOLUTION
        # self.info.algo_tasks = "OTHER"

    def create(self, param=None):
        """Instantiate algorithm object."""
        return {{ cookiecutter.class_name }}(self.info.name, param)
