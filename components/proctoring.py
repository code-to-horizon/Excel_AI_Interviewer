# components/proctoring.py
import streamlit as st
from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
from PIL import Image
import av
from streamlit_webrtc import VideoProcessorBase

# Load the model and processor from Hugging Face
# This is done once and cached for performance
@st.cache_resource
def load_model():
    processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
    model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
    return processor, model

processor, model = load_model()

class ProctoringProcessor(VideoProcessorBase):
    def __init__(self):
        self.model = model
        self.processor = processor
        self.warning_message = "No warnings."
        self.frame_count = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Convert the video frame to a PIL Image
        img = frame.to_image()
        
        # Process every 10th frame to save resources
        self.frame_count += 1
        if self.frame_count % 10 != 0:
            return av.VideoFrame.from_image(img)

        # Prepare the image for the model
        inputs = self.processor(images=img, return_tensors="pt")
        
        # Get model outputs
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Convert outputs to COCO API format and keep detections with score > 0.9
        target_sizes = torch.tensor([img.size[::-1]])
        results = self.processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

        person_count = 0
        phone_detected = False
        
        # Check for detections
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            label_name = self.model.config.id2label[label.item()]
            
            if label_name == 'person':
                person_count += 1
            if label_name == 'cell phone':
                phone_detected = True

        # Update warning message based on logic
        if person_count > 1:
            self.warning_message = "Warning: Multiple people detected."
        elif phone_detected:
            self.warning_message = "Warning: Cell phone detected."
        elif person_count == 0:
            self.warning_message = "Warning: Candidate not detected."
        else:
            self.warning_message = "Status: OK"
            
        return av.VideoFrame.from_image(img)