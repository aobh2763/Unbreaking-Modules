import sys
import os
import json
import mimetypes
import base64
from groq import Groq
from dotenv import load_dotenv
from exiftool import ExifToolHelper

load_dotenv()

exif_path = os.getenv("EXIFTOOL_PATH")

if (len(sys.argv) <= 2):
    print("No arguments provided.")
    sys.exit()

path = sys.argv[1]
options = json.loads(sys.argv[2])
mime_type, _ = mimetypes.guess_type(path)

with open(path, "rb") as f:
    image_bytes = f.read()
image_b64 = base64.b64encode(image_bytes).decode("utf-8")    
image = f"data:{mime_type};base64,{image_b64}"

with ExifToolHelper(executable=exif_path) as et:
    metadata = et.get_metadata(path)

prompt = "Transcribe this image exactly as it shows, please. Do not alter anything, just print it as is. The result should be in a strict, raw ASCII (don't put them in a code block), JSON format: The content indexed by \"content\" and another field \"success\" which is set to 1 if the transcription was successful and 0 otherwise."

client = Groq()
completion = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image}}
            ]
        }
    ],
    temperature=1,
    max_completion_tokens=1024,
    stream=False
)

response_text = completion.choices[0].message.content
print(response_text)
response_json = json.loads(response_text.strip("`"))

prompt2 = "Here is the metadata of the file, along with the text extracted from an image in the file: " + str(metadata) + "\n\nExtracted Text Content:\n" + response_json["content"] + "\n\nIn a strict JSON format, give me a authenticity score (out of 100%, indexed by \"score\") with 100% being completely authentic and 0% being absolutely forged, as well as short, brief, notes (an array indexed by \"notes\") where you detail why you came up with that answer. DON'T fact-check it! Only check the consistency of the information and its consistency with the metadata."

if "checkDates" in options:
    if options["checkDates"]:
        prompt2 += "\nConsider the file authentic if the creation/modification dates are consistent with the content of the text."
if "consistencyRules" in options:
        prompt2 += "\nAlso, apply these consistency rules when analyzing the authenticity: " + options["consistencyRules"]

client = Groq()
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": prompt2
        }
    ],
    temperature=1,
    max_completion_tokens=8192,
    top_p=1,
    reasoning_effort="medium",
    stream=False,
    stop=None
)

response_text = completion.choices[0].message.content
print(response_text)