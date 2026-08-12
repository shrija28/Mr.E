import io
import base64
from PIL import Image
from groq import Groq
import os

api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else Groq()

img = Image.new('RGB', (100, 100), color = 'white')
buffered = io.BytesIO()
img.save(buffered, format="JPEG")
img_str = base64.b64encode(buffered.getvalue()).decode()

completion = client.chat.completions.create(
    model="llama-3.2-11b-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract text"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_str}"
                    }
                }
            ]
        }
    ],
    temperature=0.0,
)
print("Groq Vision Response:", completion.choices[0].message.content)
