
import os
from pathlib import Path

import pandas as pd
import subprocess
import json
import re
# Load an Excel file and print its contents
# Ensure you have the required libraries installed:
# pip install pandas openpyxl       

# Set working directory
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

# Replace with your actual Excel file path
file_path = "./data/Rat_Monitor_reports_export_20241230.xlsx"

# === CONFIGURATION ===
EXCEL_FILE = "./data/Rat_Monitor_reports_export_20241230.xlsx"
TEXT_COLUMN = "Extra informatie\n"  # Column containing the text to process
OUTPUT_FILE = "enriched_comments.xlsx"

# === FUNCTION: Interact with Local LLM ===
def extract_rat_info(text):
    prompt = f"""
        Je taak is om gestructureerde data te extraheren als geldig JSON, met deze structuur:

        {{
        "start_date": "DD-MM-YYYY",
        "end_date": "DD-MM-YYYY",
        "brown_rats": "null of getal",
        "black_rats": "null of getal",
        "unknown_rats": "null of getal"
        }}

        Zorg voor:
        - Alleen een geldig JSON-object
        - Komma’s tussen velden
        - Geen uitleg of andere tekst
        - Sommeer aantallen indien er meerdere genoemd worden
        - Geen eenheden of labels (alleen getallen of null)
        Zin: "{text}"

        !! Antwoord ALLEEN met een JSON-object zoals !!!: 
        {{
        "start_date": "DD-MM-YYYY",
        "end_date": "DD-MM-YYYY",
        "brown_rats": getal of null,
        "black_rats": getal of null,
        "unknown_rats": getal of null
        }}
        """
    try:
        print(f"🔍 Processing text: {text[:150]}")  # Print first 50 characters for context
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        raw_output = result.stdout.decode("utf-8").strip()
        print(f"🔍 LLM Output:\n{raw_output}")
        # Extract JSON from the output, even if it's surrounded by text
        json_text = re.search(r"\{.*\}", raw_output, re.DOTALL)
        return json.loads(json_text.group()) if json_text else {}

    except Exception as e:
        print(f"⚠️ Error processing text: {text[:50]}... \n{e}")
        return {}

# === LOAD EXCEL FILE ===
df = pd.read_excel(EXCEL_FILE)

# === APPLY LLM TO EACH ROW ===
extracted = df[TEXT_COLUMN].apply(extract_rat_info)

# Convert list of dicts to DataFrame
extracted_df = pd.DataFrame(list(extracted))

# Merge with original DataFrame
merged_df = pd.concat([df, extracted_df], axis=1)

# === SAVE RESULT TO NEW FILE ===
merged_df.to_excel(OUTPUT_FILE, index=False)
print(f"✅ Saved enriched file to {OUTPUT_FILE}")

# import subprocess
# import json
# import re
# import time

# def extract_rat_data(text):
# #     prompt = f"""

# # Geef de volgende velden uit de onderstaande Nederlandse zin als JSON:
# # - start_date (eerst genoemde datum)
# # - end_date (laatst genoemde datum)
# # - brown_rats (alleen als er bruine ratten genoemd worden — tel alle aantallen op, negeer woorden als 'jonge', 'volwassen', etc.)
# # - black_rats (alleen als er zwarte ratten genoemd worden — tel alle aantallen op)
# # - unknown_rats (alleen als er ratten genoemd worden zonder kleur)

# # Let op:
# # - Soms worden meerdere aantallen ratten over meerdere datums genoemd. Tel deze aantallen bij elkaar op.
# # - Gebruik fouttolerantie voor typfouten, zoals "buine" in plaats van "bruine".
# # - Gebruik alleen hele getallen als waarden.
# # - Laat waarden leeg of null als ze ontbreken.
# # - Geef alleen een geldig JSON-object terug, zonder uitleg of extra tekst.

# # Zin: "{text}"

# # Antwoord alleen met een JSON-object zoals:
# # {{
# #   "start_date": "DD-MM-YYYY",
# #   "end_date": "DD-MM-YYYY",
# #   "brown_rats": getal of null,
# #   "black_rats": getal of null,
# #   "unknown_rats": getal of null
# # }}
# # """

#     prompt = f"""
# Je taak is om gestructureerde data te extraheren als geldig JSON, met deze structuur:

# {{
#   "start_date": "DD-MM-YYYY",
#   "end_date": "DD-MM-YYYY",
#   "brown_rats": "getal of null",
#   "black_rats": "getal of null",
#   "unknown_rats": "getal of null"
# }}

# Zorg voor:
# - Alleen een geldig JSON-object
# - Komma’s tussen velden
# - Geen uitleg of andere tekst
# - Vul alleen het veld 'brown_rats' als er bruine ratten genoemd worden (typfouten zoals "buine" tellen ook)
# - Sommeer aantallen indien er meerdere genoemd worden
# - Geen eenheden of labels (alleen getallen of null)

# Zin: "{text}"
# """
#     try:
#         start = time.time()

#         # Run model using Ollama
#         result = subprocess.run(
#             ["ollama", "run", "phi3"],  # Ensure you have the model pulled with `ollama pull mistral`
#             input=prompt.encode("utf-8"),
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             timeout=120
#         )
#         duration = time.time() - start
#         output = result.stdout.decode("utf-8")
#         print(f"🔍 LLM Output:\n{output}")
#         # Extract JSON from LLM response
#         json_match = re.search(r"\{[\s\S]*?\}", output)  # non-greedy, safer
#         if json_match:
#             try:
#                 json_data = json.loads(json_match.group(0))
#             except json.JSONDecodeError as e:
#                 print(f"⚠️ JSON decoding failed: {e}")
#                 json_data = {}
#         else:
#             print(f"⚠️ No valid JSON found in output:\n{output}")
#             json_data = {}

#         return json_data, duration  # ✅ THIS WAS MISSING

#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return {}, None

# # === Input Example ===
# example_text = """02-06 1x jonge buine rat
# 08-06 3x jonge bruine rat 
# 06-07 1x jonge bruine rat
# 24-08 1x jonge bruine rat
# 31-08 1 volwassen bruine rat
# 08-09 1x volwassen bruine rat
# 10-09 1x jonge bruine rat"""

# # example_text = """bruinerattenstraat 12"""

# print(f"\n🔍 Input: {example_text}")
# result, seconds = extract_rat_data(example_text)

# print("\n📦 Extracted JSON:")
# print(json.dumps(result, indent=2, ensure_ascii=False))

# if seconds is not None:
#     print(f"\n⏱️ Time taken: {seconds:.2f} seconds")
# else:
#     print("\n⚠️ Time not available (subprocess may have failed).")
# print("\n⚙️ Ollama uses GPU automatically if available (check terminal logs when running model).")
