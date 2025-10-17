from typing import List


class Answer:
    def __init__(self, objects: List[dict] = [], classifications: List[dict] = [], relations: List[dict] = [] ):
        self.objects = objects
        self.classifications = classifications
        self.relations = relations


    def toDict(self):
        return {
            'objects': self.objects,
            'classifications': self.classifications,
            'relations': self.relations
        }

class AnnotationPayload:
    def __init__(self, answer: Answer = None, brush_data_url: str = None, medical_brush_data_url: str = None,
                 brush_data=None, medical_brush_data=None):
        self.answer = answer
        self.brush_data_url = brush_data_url
        self.medical_brush_data_url = medical_brush_data_url
        # Optional raw brush arrays (numpy array or nested lists). If provided, SDK may upload automatically.
        self.brush_data = brush_data
        self.medical_brush_data = medical_brush_data


    def toDict(self):
        # Ensure answer always exists
        _answer = self.answer if self.answer is not None else Answer()
        return {
            'answer': _answer.toDict(),
            'brushDataUrl': self.brush_data_url,
            'medicalBrushDataUrl': self.medical_brush_data_url,
            "duration": 0
        }