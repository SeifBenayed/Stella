# Imports standards
import os
import cv2
import numpy as np
import tensorflow as tf
from datetime import datetime

# Imports TensorFlow/Keras
from tensorflow.keras.models import Model
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.resnet50 import preprocess_input

# EnhancedLongContextHandler
from handlers.handle_long_context import EnhancedLongContextHandler

# Imports Langchain
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# Imports locaux
from llms.llm import LLM, azure_supported_models, anthropic_supported_models
from utils.common_utils import beautify


class HeatmapGenerator:
    def __init__(self, persona_data: dict, lch: EnhancedLongContextHandler):
        self.persona = persona_data
        self.model = self._initialize_model()
        self.lch = lch

    def _initialize_model(self):
        # Initialisation de ResNet50 sans les couches fully connected
        base_model = ResNet50(weights='imagenet', include_top=False)

        # Création du modèle avec les sorties nécessaires pour la heatmap
        return Model(
            inputs=base_model.input,
            outputs=[
                base_model.get_layer('conv5_block3_out').output,
                base_model.output
            ]
        )

    def generate(self, image_path: str):
        # Chargement et prétraitement de l'image
        image = load_img(image_path, target_size=(512, 512))
        image_array = img_to_array(image)
        image_array = np.expand_dims(image_array, axis=0)
        image_array = preprocess_input(image_array)

        # Génération de la heatmap avec TensorFlow
        with tf.GradientTape() as tape:
            conv_output, predictions = self.model(image_array)
            weighted_predictions = self._apply_persona_weights(predictions)

        # Calcul des gradients
        grads = tape.gradient(weighted_predictions, conv_output)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        # Création et normalisation de la heatmap
        heatmap = tf.reduce_mean(tf.multiply(pooled_grads, conv_output[0]), axis=-1)
        heatmap = tf.cast(heatmap, tf.float32)
        heatmap = tf.maximum(heatmap, 0) / tf.reduce_max(heatmap)

        return heatmap.numpy()

    def _apply_persona_weights(self, predictions):
        # Application des poids basés sur les préférences du persona
        weights = np.ones_like(predictions)
        if self.persona['ux']['navigation']['mobilePriority']:
            weights *= 1.3
        return predictions * weights


@tool
def analyze_heatmap(query: str) -> str:
    """Generate and analyze heatmap based on persona preferences and previous analyses"""
    try:
        # Vérification de l'existence du screenshot
        if not os.path.exists(lch.screenshot_path):
            return "Error: Please run crawl and visual analysis first."

        # Génération de la heatmap
        heatmap_gen = ResNet50HeatmapGenerator(tools.persona)
        heatmap = heatmap_gen.generate(lch.screenshot_path)

        # Traitement de l'image
        original = cv2.imread(lch.screenshot_path)
        heatmap_resized = cv2.resize(heatmap, (original.shape[1], original.shape[0]))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Création de l'image finale
        output = cv2.addWeighted(original, 0.7, heatmap_colored, 0.3, 0)

        # Sauvegarde de la heatmap
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        heatmap_path = lch.screenshot_path.replace('.png', f'_heatmap_{timestamp}.png')
        cv2.imwrite(heatmap_path, output)

        # Préparation de l'analyse LLM
        base64_heatmap = lch.encode_image(heatmap_path)
        llm = LLM(os.getenv("llm_id")).get_llm()

        # Création du prompt d'analyse
        analysis_prompt = f"""
        Analyze this heatmap for {tools.persona['name']}, focusing on:
        1. Attention patterns matching their needs: {', '.join(tools.persona['nmb']['needs'])}
        2. Mobile usability: {tools.persona['ux']['navigation']['mobilePriority']}
        3. Visual hierarchy for their {tools.persona['ux']['visualStyle']['designStyle']} design preference
        4. Potential barriers: {', '.join(tools.persona['nmb']['barriers'])}

        Consider previous visual and textual analyses to provide comprehensive insights.
        """

        # Configuration des messages selon le type de modèle
        if os.getenv("llm_id") in azure_supported_models:
            messages = [
                {"role": "system", "content": "You are a UX analysis expert"},
                {"role": "user", "content": [
                    {"type": "text", "text": analysis_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_heatmap}"}}
                ]}
            ]
        else:  # anthropic_supported_models
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_heatmap}"}}
                    ]
                )
            ]

        # Obtention et sauvegarde de l'analyse
        result = llm.invoke(messages)

        lch.append_to_agent_scratchpad(
            f"Heatmap Analysis for {tools.persona['name']}:\n{result.content}",
            "analyze_heatmap"
        )

        return f"Heatmap analysis completed and saved. Heatmap path: {heatmap_path}"

    except Exception as e:
        error_msg = f"Error in heatmap analysis: {str(e)}"
        lch.append_to_agent_scratchpad(error_msg, "analyze_heatmap")
        return error_msg