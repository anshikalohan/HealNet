import io
import numpy as np
from PIL import Image
from app.core.config import settings
from app.utils.constants import CLASSES_MAPPING, DISCLAIMER

import tensorflow as tf
from tensorflow.keras.models import load_model # type: ignore

tf.config.set_visible_devices([], 'GPU')

def try_load_model(path):
    try:
        model = load_model(path)
        print(f"✅ Loaded model: {path}")
        return model
    except Exception as e:
        print(f"❌ Failed to load model {path}: {e}")
        return None

modality_classifier = try_load_model(f"{settings.MODELS_PATH}/modality_classifier.h5")
brain_tumor_classifier = try_load_model(f"{settings.MODELS_PATH}/brain_tumor_classifier.h5")
skin_cancer_model = try_load_model(f"{settings.MODELS_PATH}/Skin_Cancer.h5")
lung_model = try_load_model(f"{settings.MODELS_PATH}/lung_model.keras")

def preprocess_image(image_bytes, target_size=(256, 256), scaling='none'):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(target_size)
    img_array = np.array(img, dtype=np.float32)
    
    if scaling == '1/255':
        img_array = img_array / 255.0
    elif scaling == 'xception':
        img_array = (img_array / 127.5) - 1.0
        
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def analyze_medical_image(image_bytes, language='english'):
    if not modality_classifier:
        return "Models not available." + DISCLAIMER
    
    try:
        # Step 1: Modality classification (EfficientNet expects 0-255 pixels, scaling='none')
        img_array = preprocess_image(image_bytes, target_size=(224, 224), scaling='none')
        
        modality_preds = modality_classifier.predict(img_array)[0]
        modality_idx = int(np.argmax(modality_preds))
        
        if modality_idx == 0:
            modality = "brain"
            model = brain_tumor_classifier
            target_size = (299, 299)
            scaling = '1/255'
        elif modality_idx == 1:
            modality = "lung"
            model = lung_model
            target_size = (256, 256)
            scaling = '1/255'
        elif modality_idx == 2:
            modality = "skin"
            model = skin_cancer_model
            target_size = (224, 224)
            scaling = 'none'
        else:
            return "Unable to determine image modality." + DISCLAIMER
            
        if not model:
            return f"{modality.capitalize()} model not available." + DISCLAIMER
            
        img_array = preprocess_image(image_bytes, target_size=target_size, scaling=scaling)
            
        if modality == "brain":
            preds = model.predict(img_array)[0]
            pred_idx = np.argmax(preds)
            pred_class = CLASSES_MAPPING["brain"][pred_idx]
            conf = float(preds[pred_idx] * 100)
            
            if language == 'hindi':
                response = f"🧠 *ब्रेन एमआरआई विश्लेषण*\n\n🔎 स्थिति: *{pred_class}*\nविश्वास स्तर: {conf:.1f}%\n\n⚠️ कृपया डॉक्टर से पुष्टि कराएं।"
            else:
                response = f"🧠 *Brain MRI Analysis*\n\n🔎 Condition: *{pred_class}*\nConfidence: {conf:.1f}%\n\n⚠️ Please consult a doctor for confirmation."
                
        elif modality == "skin":
            preds = model.predict(img_array)[0]
            if len(preds) == 1:
                prob = float(preds[0])
                pred_class = CLASSES_MAPPING["skin"][1] if prob > 0.5 else CLASSES_MAPPING["skin"][0]
                conf = prob * 100 if prob > 0.5 else (1 - prob) * 100
            else:
                pred_idx = np.argmax(preds)
                pred_class = CLASSES_MAPPING["skin"][pred_idx]
                conf = float(preds[pred_idx] * 100)
                
            if language == 'hindi':
                response = f"🔍 *त्वचा विश्लेषण*\n\n🔎 स्थिति: *{pred_class}*\nविश्वास स्तर: {conf:.1f}%\n\n⚠️ कृपया डॉक्टर से पुष्टि कराएं।"
            else:
                response = f"🔍 *Skin Lesion Analysis*\n\n🔎 Condition: *{pred_class}*\nConfidence: {conf:.1f}%\n\n⚠️ Please consult a doctor for confirmation."
                
        elif modality == "lung":
            preds = model.predict(img_array)[0]
            preds_prob = 1 / (1 + np.exp(-preds)) if np.max(preds) > 1 else preds
            
            no_finding_idx = CLASSES_MAPPING["lung"].index("No_Finding")
            no_finding_conf = float(preds_prob[no_finding_idx] * 100)
            
            pathology_findings = []
            for i in range(14):
                if CLASSES_MAPPING["lung"][i] != "No_Finding" and preds_prob[i] > 0.3:
                    pathology_findings.append((CLASSES_MAPPING["lung"][i], float(preds_prob[i] * 100)))
                    
            pathology_findings = sorted(pathology_findings, key=lambda x: x[1], reverse=True)
            
            if no_finding_conf > 50 and len(pathology_findings) == 0:
                if language == 'hindi':
                    response = f"🩻 *छाती एक्स-रे विश्लेषण*\n\n✅ कोई स्पष्ट असामान्यता नहीं पाई गई\nविश्वास स्तर: {no_finding_conf:.1f}%\n\nफिर भी यदि लक्षण हैं तो डॉक्टर से परामर्श करें।"
                else:
                    response = f"🩻 *Chest X-ray Analysis*\n\n✅ No significant abnormality detected\nConfidence: {no_finding_conf:.1f}%\n\nConsult a doctor if symptoms persist."
            else:
                if language == 'hindi':
                    response = "🩻 *छाती एक्स-रे विश्लेषण*\n\n🔎 संभावित स्थितियां:\n"
                    for label, conf in pathology_findings[:5]:
                        response += f"• {label} — {conf:.1f}%\n"
                    response += f"\n📊 सामान्य होने की संभावना: {no_finding_conf:.1f}%\n\n⚠️ कृपया डॉक्टर से पुष्टि कराएं।"
                else:
                    response = "🩻 *Chest X-ray Analysis*\n\n🔎 Detected Potential Conditions:\n"
                    for label, conf in pathology_findings[:5]:
                        response += f"• {label} — {conf:.1f}%\n"
                    response += f"\n📊 Normal probability: {no_finding_conf:.1f}%\n\n⚠️ Please consult a doctor for confirmation."

        return response + DISCLAIMER
    
    except Exception as e:
        print(f"Medical analysis error: {e}")
        return "Failed to analyze image." + DISCLAIMER
