import torch
from transformers import AutoTokenizer, AutoModel

model_name = "Omartificial-Intelligence-Space/Arabert-all-nli-triplet-Matryoshka"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# just checking if cuda is activated
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
model = model.to(device)

sample_text = "الذكاء الاصطناعي يساعد الشركات على التطور"
inputs = tokenizer(sample_text, return_tensors="pt", truncation=True, padding=True).to(device)
with torch.no_grad():
    outputs = model(**inputs)

print("Model outputs keys:", outputs.keys())
if hasattr(outputs, "last_hidden_state"):
    embeddings = outputs.last_hidden_state[:, 0, :]
    print("Embedding shape:", embeddings.shape)
    print("First 5 values:", embeddings[0][:5])
