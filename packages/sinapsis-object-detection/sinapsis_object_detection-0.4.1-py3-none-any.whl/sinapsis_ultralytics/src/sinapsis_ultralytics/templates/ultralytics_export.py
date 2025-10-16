# -*- coding: utf-8 -*-

from pydantic import Field
from sinapsis_core.data_containers.data_packet import DataContainer
from sinapsis_core.utils.env_var_keys import WORKING_DIR
from ultralytics.utils.files import WorkingDirectory

from sinapsis_ultralytics.helpers.params import ExportParams
from sinapsis_ultralytics.helpers.tags import Tags
from sinapsis_ultralytics.templates.ultralytics_base import UltralyticsBase

UltralyticsExportUIProperties = UltralyticsBase.UIProperties
UltralyticsExportUIProperties.tags.extend([Tags.EXPORT, Tags.ONNX, Tags.TENSORFLOW, Tags.TENSORRT])


class UltralyticsExport(UltralyticsBase):
    """Template to export ultralytics models to different formats such as ONNX, TensorFlow, TensorRT, etc. The exported
    model is saved in the working directory.

    More info can be found at https://docs.ultralytics.com/modes/export/#usage-examples


    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UltralyticsExport
      class_name: UltralyticsExport
      template_input: InputTemplate
      attributes:
        model_class: 'YOLO'
        model: yolo11n-cls.pt
        task: detect
        verbose: true
        working_dir: /path/to/cache/dir
        datasets_dir: /path/to/ultralytics/dataset/dir
        run_id: null
        checkpoint_name: last.pt
        checkpoint_path: null
        export_params:
            format : onnx
            optimize : True


    """

    UIProperties = UltralyticsExportUIProperties

    class AttributesBaseModel(UltralyticsBase.AttributesBaseModel):
        """
        Attributes for Ultralytics Export Template

        export_params (ExportParams): ExportParams containing the parameters
        required to export an Ultralytics model to a desired format.
        If not specified, model will be exported using default parameters.


        Detailed description of available export parameters can be found in:
        https://docs.ultralytics.com/modes/export/#arguments
        """

        export_params: ExportParams = Field(default_factory=ExportParams)

    def execute(self, container: DataContainer) -> DataContainer:
        with WorkingDirectory(WORKING_DIR):
            exported_path = self.model.export(**self.attributes.export_params.model_dump())
            self.logger.info(f"Model exported to {exported_path}")

        return container
