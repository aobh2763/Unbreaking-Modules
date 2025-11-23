import sys
import mimetypes
import base64
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()

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

if "fontTolerance" in options:
    font_tolerance = "\nGive a font accuracy score (out of 100), consider a font tolerance of: " + options["fontTolerance"] + " out of 1 (indexed by \"fontScore\")."

prompt = "Transcribe this image exactly as it shows, please. Do not alter anything, just print it as is. The result should be in a strict, raw ASCII (don't put them in a code block), JSON format: The content indexed by \"content\" and another field \"success\" which is set to 1 if the transcription was successful and 0 otherwise." + font_tolerance

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

plagiarism_check = ""
font_tolerance = ""
regex_checks = ""

if "plagiarismCheck" in options:
    plagiarism_check = "\nIt's " + options["plagiarismCheck"] + " that you must check for plagiarism in the content."
if "regexChecks" in options:
    regex_checks = "\nAlso, apply these regex checks on the content: " + options["regexChecks"]
if "fontTolerance" in options:
    font_tolerance = "\nAlso, know that the vision model gave a font accuracy score of " + str(response_json.get("fontScore")) + " out of 100."

if response_json["success"] != 1:
    print("Transcription was not successful.")
    sys.exit()

prompt2 = "Context : We are trying to determine if the following text is historically accurate, check reliable, trustworthy sources to assign it an accuracy score (check for bias, inconsistencies or just straight up misinformation). Please be thorough.\nIn a strict JSON format, give me the accuracy score (out of 100%, indexed by \"score\") with 100% being completely true and 0% being absolutely wrong, as well as short, brief, notes (an array indexed by \"notes\") where you detail why you came up with that answer." + regex_checks + plagiarism_check + "\nHere is the content :" + response_json.get("content")

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

response_text2 = completion.choices[0].message.content
print(response_text2)