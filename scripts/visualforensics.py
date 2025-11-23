import cv2
import numpy as np
import os
import sys
import json

if (len(sys.argv) <= 2):
    print("No arguments provided.")
    sys.exit()

path = sys.argv[1]
options = json.loads(sys.argv[2])

prompt = ""
detection_threshold = 0.8

if "detectionThreshold" in options:
    detection_threshold = float(options["detectionThreshold"])
if "colorChannels" in options:
    match options["colorChannels"]:
        case "grayscale":
            channel = cv2.IMREAD_GRAYSCALE
        case "RGB":
            channel = cv2.IMREAD_COLOR
if "noiseFilter" in options:
    noise_filter = options["noiseFilter"]

def ela_score(img):
    """Error Level Analysis score: high difference means potential edits."""
    cv2.imwrite("tmp_ela.jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    recompressed = cv2.imread("tmp_ela.jpg")

    diff = cv2.absdiff(img, recompressed)
    score = np.mean(diff)
    os.remove("tmp_ela.jpg")
    return score

def sharpness_score(gray):
    """Variance of Laplacian measures edge strength. Inconsistent sharpness may indicate edits."""
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def noise_score(gray):
    """Check pixel noise consistency."""
    noise = cv2.GaussianBlur(gray, (3,3), 0)
    diff = cv2.absdiff(gray, noise)
    return np.mean(diff)

def remove_noise(image):
    """
    Remove noise from a document image.
    Accepts either grayscale or color.
    Returns cleaned image.
    """

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    return denoised

def texture_uniformity(gray):
    """Measure texture entropy. Manipulated areas may have unnatural entropy differences."""
    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    hist_norm = hist / hist.sum()
    entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-9))
    return float(entropy)


def keypoint_density(gray):
    """Detect copy-paste patterns based on feature richness."""
    orb = cv2.ORB_create()
    kp, _ = orb.detectAndCompute(gray, None)
    return len(kp)


def get_image_stats(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Image could not be loaded.")
    
    if "noiseFilter" in options:
        img = remove_noise(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    values = {}

    values["resolution"] = f"{img.shape[1]}x{img.shape[0]} px"
    values["channels"] = img.shape[2] if len(img.shape) == 3 else 1

    values["sharpness (variance of Laplacian)"] = round(sharpness_score(gray), 2)
    values["noise consistency score"] = round(noise_score(gray), 2)
    values["texture entropy"] = round(texture_uniformity(gray), 2)
    values["ELA anomaly score"] = round(ela_score(img), 2)
    values["keypoint complexity"] = keypoint_density(gray)

    return values

results = get_image_stats(path)

prompt = "In a raw plain text JSON object, Analyze the following image statistics for potential signs of manipulation or forgery. Provide an authenticity likelihood score (0-100%) (indexed by 'score') and brief notes explaining your reasoning (an array of brief notes, indexed by 'notes').\n\nImage Statistics:\n" + str(results) + "\n\nConsider the following thresholds for analysis:\n- Sharpness (Variance of Laplacian): Low values may indicate blurring or smoothing.\n- Noise Consistency Score: High inconsistency may suggest localized edits.\n- Texture Entropy: Unnatural entropy variations can signal tampering.\n- ELA Anomaly Score: Higher scores often point to modifications.\n- Keypoint Complexity: Low complexity may indicate copy-paste forgeries." + "\nForgery Likelihood Threshold: " + str(detection_threshold*100) + "%"

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

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
    max_completion_tokens=2048,
    top_p=1,
    reasoning_effort="medium",
    stream=False,
    stop=None
)

response_text = completion.choices[0].message.content
print(response_text)