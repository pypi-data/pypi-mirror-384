![hawkeye_banner (1)](https://github.com/user-attachments/assets/2fc19973-58b3-459d-9dd0-968a7ba8cbc4)

Hawkeye-Zero - special trained model to detect 11 diffrent types of space debris. 
The idea wasn’t to build a perfect system — just to explore how far object detection can go in real-world space debris applications.
It’s still early, but the results are promising. The model's trained on YOLO11 model created from ultralytics. Also very important thing was to care about easy and quick access to use model functions and data, so I've created special structure for this project to allowed developers to use model in diffrent environments in API's or as a simple python tool.

## 📄 Docs
[![PyPI - Version](https://img.shields.io/pypi/v/ultralytics?logo=pypi&logoColor=white)]()  [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ultralytics?logo=python&logoColor=gold)]()

[Read documentation->]()


### Usage
#### Python
```python
from hawkeyeZero import HawkeyeZero

hawkeye = HawkeyeZero(is_dev_mode=True)

hawkeye.use_model()
```

## 🤝 Contributing
That would be a huge pleasure to make this project better, because of your job, so if you want to help me out with this project [Check out this file]()

## 📜License
Current license: [AGPL-3.0 License](https://github.com/Gabrli/Hawkeye-Zero/blob/main/LICENSE)
## 📘Used dataset
[Read more](https://www.kaggle.com/datasets/muhammadzakria2001/space-debris-detection-dataset-for-yolov8?select=data.yaml)

## 📞 Contact
For bug reports and feature requests related to Hawkeye-Zero software, please visit GitHub Issues. For questions, discussions, and community support.




