from types import MappingProxyType

from scaledp.models.detectors.YoloOnnxDetector import YoloOnnxDetector
from scaledp.enums import Device


class FaceDetector(YoloOnnxDetector):
    defaultParams = MappingProxyType(
        {
            "inputCol": "image",
            "outputCol": "boxes",
            "keepInputData": False,
            "scaleFactor": 1.0,
            "scoreThreshold": 0.2,
            "device": Device.CPU,
            "batchSize": 2,
            "partitionMap": False,
            "numPartitions": 0,
            "pageCol": "page",
            "pathCol": "path",
            "propagateError": False,
            "task": "detect",
            "onlyRotated": False,
            "model": "StabRise/face_detection"
        },
    )
