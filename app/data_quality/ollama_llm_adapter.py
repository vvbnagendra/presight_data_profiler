import requests
from pandasai.llm.base import LLM

# -------------------------------
# Custom LLM Adapter for Ollama
# -------------------------------
class OllamaLLM(LLM):
    def __init__(self, model="deepseek-r1:1.5b", base_url="http://localhost:11434", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.base_url = base_url  # base_url should not include the /api/generate part

    def call(self, instruction, context=None, **kwargs):
        # Convert instruction object (e.g. GeneratePythonCodePrompt) to string
        prompt_str = str(instruction)

        # Send prompt to Ollama API
        response = requests.post(
            f"{self.base_url}/api/generate",  # Correct full endpoint here
            json={
                "model": self.model,
                "prompt": prompt_str,
                "stream": False
            }
        )

        # Debug raw output
        print("Raw response:")
        print(response.text)

        # Safely parse JSON if it looks valid
        try:
            json_data = response.json()
            print("Parsed response:", json_data)
            return json_data["response"]  # Return the actual generated response
        except requests.exceptions.JSONDecodeError:
            print("⚠️ Could not parse JSON from the response.")
            return None

    @property
    def type(self):
        return "ollama"
