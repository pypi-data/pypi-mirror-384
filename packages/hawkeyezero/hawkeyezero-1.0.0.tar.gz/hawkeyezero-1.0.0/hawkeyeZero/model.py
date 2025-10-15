from ultralytics import YOLO
from .constants import MODEL_PARAMETERS, MODEL_AGUMENT_PARAMETERS, MODELS_TO_USE

class HawkeyeZero():
    def __init__(self, is_dev_mode=False, model_to_use="best.pt") -> None:
        """
        Method to initiate HawkeyeZero object.
        Args:
            is_dev_mode (bool): Parameter to set if software has to work in developer mode.
            model_to_use (str): model selected to training.
        """
        self.model_to_use = model_to_use
        self._model = None
        self.is_dev_mode = is_dev_mode
        self._data = None

    def _load_path(self, abs, join) -> str:
        """
        Method to load paths.

        Args:
            abs (str): end point of fetching absolute path.
            join (str): path which is expected as wanted
        """
        import os
        current_dir = os.path.dirname(os.path.abspath(abs))
        return os.path.join(current_dir, join)
    
    def _load_yolo(self) -> None:
        """
        Method to load expected to use by user model.
        """
        is_model_avaliable = self._is_model_avaliable()
        if is_model_avaliable:

            model_path = self._load_path(__file__, f'model/{MODEL_PARAMETERS['name']}/weights/{self.model_to_use}')
   
            self._model = YOLO(self.model_to_use if self.model_to_use == "yolo11n.pt" else model_path)

    def _is_model_avaliable(self) -> bool:
        """
        Method to check if expected model by user is in avaliable models list.

        Returns:
            (bool): True if model is in model list.
        """
        return True if self.model_to_use in MODELS_TO_USE else False
    
    def _draw_ui_detection_results(self, result) -> None:
        """
        Method to draw UI for detection results.

        Args:
            results (list): results of detection.
        """
        import cv2
        from matplotlib import pyplot as plt
        annotated_frame = result.plot()


        plt.figure(figsize=(10, 10))
        plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
        plt.axis("off")
        plt.title("Detected objects")
        plt.show()

    def use_model(self, input_data=None, display_results=True) -> any:
        """
        Method allowed for developers to use model in 2 diffrent situations.
        Args:
            input_data (str): path to img.
            dispaly_results (bool): If True, draw and open window app with displayed detection on img.

        Returns:
            (str | Any): If input_data is none and dev mode is switch to false, return str, else return Any, because method is returning nothing.
        """
        self._load_yolo()
        if self.is_dev_mode:
            self._data = self._load_path('dataset', 'dataset/data.yaml')
            self._train()
        if input_data is None and not self.is_dev_mode:
            return "Empty input_data parameter."
        
        results = self._model(input_data)
        if display_results:
            self._draw_ui_detection_results(results[0])
      

        return results
       
        
      
    def _train(self) -> None:
        """
        Method to initiate model training with prepered model parameters.
        """
        project_path = self._load_path(__file__, 'model')


        self._model.train(data=self._data, project=project_path, **MODEL_PARAMETERS, **MODEL_AGUMENT_PARAMETERS)

    
    def val(self) -> None:
        """
        Method allowed for users.
        Method to validate model.
        """
        self._model.val(self._data)
    
    def export(self, args) -> None:
        """
        Method allowed for users.
        Method to export model to avaliable formats with diffrent parameters.

        Args:
            args (tuple): parameters for export proccess.
        """
        self._model.export(**args)

    