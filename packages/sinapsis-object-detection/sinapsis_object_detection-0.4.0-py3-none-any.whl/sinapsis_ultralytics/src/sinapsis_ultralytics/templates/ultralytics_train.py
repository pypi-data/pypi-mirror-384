# -*- coding: utf-8 -*-

from pydantic import Field
from sinapsis_core.data_containers.data_packet import DataContainer
from ultralytics.utils.files import WorkingDirectory

from sinapsis_ultralytics.helpers.params import TrainParams
from sinapsis_ultralytics.helpers.tags import Tags
from sinapsis_ultralytics.templates.ultralytics_base import UltralyticsBase

UltralyticsTrainUIProperties = UltralyticsBase.UIProperties
UltralyticsTrainUIProperties.tags.extend([Tags.DATASET, Tags.TRAINING])


class UltralyticsTrain(UltralyticsBase):
    """
    Template to train an ultralytics model

    The template includes functionality to train: "YOLO", "YOLOWorld", "SAM", "FastSAM", "NAS", "RTDETR",
    configurable through the attributes of the template. This includes the number of epochs, the task,
    the dataset to use for the training, etc.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UltralyticsTrain
      class_name: UltralyticsTrain
      template_input: InputTemplate
      attributes:
        model_class: YOLO
        model: yolo11n.pt
        task: detect
        verbose: 0
        training_params:
          data: "signature.yaml"
          epochs: 2
          imgsz: 128
          batch: 32
          device: 0

    """

    UIProperties = UltralyticsTrainUIProperties

    class AttributesBaseModel(UltralyticsBase.AttributesBaseModel):
        """
        Attributes for UltralyticsTrain Template

        Args:
            training_params (TrainParams): TrainParams containing the training parameters for
                the Ultralytics model. If not specified, default parameters will be used.

            The full documentation for available training parameters can be found in the Ultralytics docs:
            https://docs.ultralytics.com/modes/train/#train-settings
        """

        training_params: TrainParams = Field(default_factory=TrainParams)

    def execute(self, container: DataContainer) -> DataContainer:
        """
        Executes Ultralytics model training.

        Args:
            container (DataContainer): A container holding the data to be processed.
        Returns:
            DataContainer: The container with updated metrics and model path after training.
        """
        with WorkingDirectory(self.attributes.working_dir):
            # Train the model using the training parameters
            trained_model = self.model.train(**self.attributes.training_params.model_dump())

            # Store the model's metrics and the trained model's directory path
            model_info = {
                "metrics": self.model.metrics.to_df(),
                "trained_model_path": str(trained_model.save_dir),
            }
            self._set_generic_data(container, model_info)

        return container
