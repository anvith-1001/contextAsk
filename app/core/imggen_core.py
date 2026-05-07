from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from google import genai
import base64
import os


class ImageGenCore:

    def __init__(self, chat_message_core):
        mongo_client = MongoClient(os.getenv("MONGO_URI"))
        db = mongo_client["rag_db"]

        self.collection = db["generated_images"]
        self.chat_message_core = chat_message_core

        self.gemini_client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY")
        )

        self.model = os.getenv(
            "GOOGLE_IMAGE_MODEL",
            "gemini-2.5-flash-image"
        )

    def build_prompt(self, query, context, history):
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history
        ])

        context_text = "\n".join([
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in context
        ])

        prompt = f"""Create a high-quality visual image based on the user's request.

User Request:
{query}

Relevant Context (use only if visually relevant):
{context_text}

Conversation History (use only if helpful):
{history_text}

Image Requirements:
- Safe for work and free of harmful or explicit content
- Clear and visually appealing composition
- Strong focus on the main subject
- Coherent environment and background
- Natural lighting and realistic textures
- Sharp details and balanced framing
- No text, captions, labels, logos, or watermarks unless explicitly requested
- Avoid diagrams, charts, or infographics unless requested
- Avoid blurry, distorted, deformed, low-quality, cluttered, cropped, or duplicated subjects
- Maintain realistic anatomy and proportions
- Keep the image visually clean and professional
"""

        return prompt.strip()

    def _extract_image_from_gemini_response(self, response):
      if not response.candidates:
          raise ValueError("Gemini did not return any candidates")

      parts = response.candidates[0].content.parts or []
      text_parts = []

      for part in parts:
          if getattr(part, "inline_data", None):
              image_bytes = part.inline_data.data
              mime_type = part.inline_data.mime_type or "image/png"
              return image_bytes, mime_type

          if getattr(part, "text", None):
              text_parts.append(part.text)

      text_response = " ".join(text_parts).strip()

      if text_response:
          raise ValueError(f"Gemini returned text instead of image: {text_response}")

      raise ValueError("Gemini response did not contain image data")


    def generate_image(self, query, user_id, chat_id, context=None, history=None):
        context = context or []
        history = history or []

        prompt = self.build_prompt(
            query=query,
            context=context,
            history=history
        )

        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        image_bytes, mime_type = self._extract_image_from_gemini_response(response)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        image_doc = {
            "chat_id": chat_id,
            "user_id": user_id,
            "prompt": prompt,
            "image_base64": image_base64,
            "mime_type": mime_type,
            "created_at": datetime.utcnow()
        }

        result = self.collection.insert_one(image_doc)
        image_id = str(result.inserted_id)

        self.chat_message_core.save_message(
            chat_id=chat_id,
            user_id=user_id,
            role="assistant",
            content={
                "type": "image",
                "image_id": image_id,
                "message": "Generated image"
            }
        )

        return {
            "success": True,
            "image_id": image_id,
            "mime_type": mime_type,
            "image_base64": image_base64
        }

    def get_image(self, image_id, user_id):
        if not ObjectId.is_valid(image_id):
            return None

        image = self.collection.find_one({
            "_id": ObjectId(image_id),
            "user_id": user_id
        })

        if not image:
            return None

        return {
            "image_id": str(image["_id"]),
            "chat_id": image["chat_id"],
            "mime_type": image.get("mime_type", "image/png"),
            "image_base64": image["image_base64"],
            "prompt": image["prompt"]
        }

    def list_images(self, user_id):
        images = self.collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1)

        return [
            {
                "image_id": str(image["_id"]),
                "chat_id": image.get("chat_id"),
                "mime_type": image.get("mime_type", "image/png"),
                "image_base64": image.get("image_base64"),
                "image_url": (
                    f"data:{image.get('mime_type', 'image/png')};base64,{image.get('image_base64')}"
                    if image.get("image_base64")
                    else None
                ),
                "prompt": image.get("prompt"),
                "created_at": image.get("created_at")
            }
            for image in images
        ]

    def delete_image(self, image_id, user_id):
        if not ObjectId.is_valid(image_id):
            return None

        result = self.collection.delete_one({
            "_id": ObjectId(image_id),
            "user_id": user_id
        })

        return result.deleted_count > 0