import os
import openai

# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_API_KEY")

prompt = """
Japanese: わたしは　にほんごがすこししかはなせません。
English: Unfortunately, I speak only a little Japanese..
Japanese:
"""

response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=5
    )
