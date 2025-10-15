from .model_setup_parameters import epochs, batch, summary_name, imgsz, exist_ok

from .model_agument_parameters import fliplr, flipud, hsv_h, hsv_s, hsv_v, translate, scale, shear, perspective, mixup, mosaic

from .models_to_use import MODELS_TO_USE


MODEL_AGUMENT_PARAMETERS = {
    'fliplr': fliplr,
    'flipud': flipud,
    'hsv_h': hsv_h,
    'hsv_s': hsv_s,
    'hsv_v': hsv_v,
    'translate': translate,
    'scale': scale,
    'shear': shear,
    'perspective': perspective,
    'mixup': mixup,
    'mosaic': mosaic
}

MODEL_PARAMETERS = {
    'epochs': epochs,
    'batch': batch,
    'name':summary_name,
    'imgsz':imgsz,
    'exist_ok':exist_ok
}