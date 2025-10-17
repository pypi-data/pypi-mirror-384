
filename = "backend.py"
content = """
import torch
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from transformers import T5EncoderModel
from dequantor import StableDiffusion3Pipeline, GGUFQuantizationConfig, SD3Transformer2DModel
from io import BytesIO
import base64
app = FastAPI(title="GGUF API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32
print(f"Device detected: {device}")
print(f"torch version: {torch.__version__}")
print(f"dtype using: {dtype}")
model_path = "https://huggingface.co/calcuis/sd3.5-lite-gguf/blob/main/sd3.5-2b-lite-q4_0.gguf"
transformer = SD3Transformer2DModel.from_single_file(
    model_path,
    quantization_config=GGUFQuantizationConfig(compute_dtype=dtype),
    torch_dtype=dtype,
    config="callgg/sd3-decoder",
    subfolder="transformer_2"
)
text_encoder = T5EncoderModel.from_pretrained(
    "chatpig/t5-v1_1-xxl-encoder-fp32-gguf",
    gguf_file="t5xxl-encoder-fp32-q2_k.gguf",
    torch_dtype=dtype
)
pipe = StableDiffusion3Pipeline.from_pretrained(
    "callgg/sd3-decoder",
    transformer=transformer,
    text_encoder_3=text_encoder,
    torch_dtype=dtype
)
pipe.enable_model_cpu_offload()
@app.post("/generate")
def generate_image(
    prompt: str = Form(...),
    num_steps: int = Form(8),
    guidance: float = Form(2.5)
):
    image = pipe(
        prompt,
        height=1024,
        width=1024,
        num_inference_steps=num_steps,
        guidance_scale=guidance,
    ).images[0]
    # Convert to base64 to send back to frontend
    buf = BytesIO()
    image.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return JSONResponse({"image": encoded})
"""

with open(filename, "w") as f:
    f.write(content)

import os
os.system("uvicorn backend:app --reload --port 8000")