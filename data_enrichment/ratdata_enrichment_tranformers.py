import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, modeling_utils

torch.cuda.empty_cache()
if not hasattr(modeling_utils, "ALL_PARALLEL_STYLES") or modeling_utils.ALL_PARALLEL_STYLES is None:
    modeling_utils.ALL_PARALLEL_STYLES = ["tp", "none","colwise",'rowwise']

def predict_NuExtract(model, tokenizer, texts, template, batch_size=1, max_length=8_000, max_new_tokens=2_000):
    template = json.dumps(json.loads(template), indent=4)
    prompts = [f"""<|input|>\n### Template:\n{template}\n### Text:\n{text}\n\n<|output|>""" for text in texts]
    
    outputs = []
    with torch.no_grad():
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i+batch_size]
            batch_encodings = tokenizer(batch_prompts, return_tensors="pt", truncation=True, padding=True, max_length=max_length).to(model.device)

            pred_ids = model.generate(**batch_encodings, max_new_tokens=max_new_tokens)
            outputs += tokenizer.batch_decode(pred_ids, skip_special_tokens=True)

    return [output.split("<|output|>")[1] for output in outputs]

model_name = "numind/NuExtract-tiny-v1.5"
device = "cuda"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, trust_remote_code=True).to(device).eval()
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

text = """van 12 tot 18-11, 6 bruine ratten""" 

template = """{
    "Amount of rats": {
        "bruin": 0,
        "zwart": 0,
        "": 0
    },
    "Dates": {
        "First Date": "DD-MM",
        "Last Date": "DD-MM"
    }
}"""

prediction = predict_NuExtract(model, tokenizer, [text], template)[0]
print(prediction)
