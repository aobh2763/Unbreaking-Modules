import sys
import os
from groq import Groq
from dotenv import load_dotenv
from exiftool import ExifToolHelper

load_dotenv()

exif_path = os.getenv("EXIFTOOL_PATH")

if (len(sys.argv) <= 1):
    print("No arguments provided.")
    sys.exit()

path = sys.argv[1]

with ExifToolHelper(executable=exif_path) as et:
    metadata = et.get_metadata(path)

prompt = "Context : We are trying to determine if a file has been tampered with / displays any signs of suspicious behavior using metadata analysis.\n Here is the file's metadata :" + str(metadata) + "\n\nIn a strict JSON format, give me a authenticity score (out of 100%, indexed by \"score\") with 100% being completely authentic and 0% being absolutely forged, as well as short, brief, notes (an array indexed by \"notes\") where you detail why you came up with that answer."

client = Groq()
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": prompt
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