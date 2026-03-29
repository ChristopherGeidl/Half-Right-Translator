import warnings
# This ignores the 'pin_memory' warning
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.data.dataloader")

import easyocr
import os

class Reader:
    def __init__(self, lang_list=['ch_sim', 'en']):
        self.reader = easyocr.Reader(lang_list, gpu=True)

    def verify_text(self, image_path, target):
        result = self.reader.readtext(image_path, detail=1)
        
        if not result:
            return False, "", 0.0

        full_detected_text = ""
        total_confidence = 0
        
        for (bbox, text, prob) in result:
            full_detected_text += text.replace(" ", "")
            total_confidence += prob
        
        avg_confidence = total_confidence / len(result)

        is_correct = (full_detected_text == target)
        return is_correct, full_detected_text, avg_confidence