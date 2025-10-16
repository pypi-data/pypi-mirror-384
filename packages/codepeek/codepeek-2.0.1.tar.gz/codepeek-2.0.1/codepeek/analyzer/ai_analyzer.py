import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


class AIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("❌ MISTRAL_API_KEY not found in environment variables.")

        self.model = "mistral-small"
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_recommendations(self, summary_json: dict):
        print("🧠 Sending project summary to Mistral for analysis...")

        prompt = """
You are a **Senior Software Architect & Code Reviewer** specializing in Flutter,Andriod, IOS, front-end , backend, AI , and Clean Architecture design.

Your job is to perform an in-depth technical review of this project summary.

🔍 **Goals:**
- Detect violations of the SOLID principles and explain why each one is a violation.
- Detect design patterns used or missing, and recommend better alternatives where applicable.
- Identify security issues (hardcoded secrets, weak validation, unsafe state management, data exposure, insecure API handling, etc.).
- Evaluate architecture quality — separation of layers, dependency flow, state management, reusability, and scalability.
- Provide final recommendations for maintainability, testability, and performance.

🚫 **Ignore Completely:**
- Auto-generated code, build/ or .dart_tool/ or node_modules/, .gradle/, .idea/, etc.
- Assets, fonts, images, icons, JSONs, or environment files that don't contain logic.
- Boilerplate setup like main.dart with only MaterialApp.

✅ **Focus On:**
- Files under `lib/`, `src/`, `core/`, `app/`, `data/`, `domain/`, `presentation/`.....etc.
- Service classes, repository patterns, ViewModels, and widgets.
- Whether dependency inversion is respected, if logic is leaking between layers, or if UI depends on data sources directly.
- UI performance at all 

🧱 **SOLID Check Examples:**
- SRP: Class handles multiple responsibilities.
- OCP: Hardcoded logic instead of extendable design.
- LSP: Derived widget breaking base behavior.
- ISP: Fat interfaces or large service contracts.
- DIP: UI directly calling repositories or APIs.

🧩 **Design Pattern Examples:**
Factory, Singleton, Strategy, Observer, Repository, Provider, Command, MVC/MVVM, Builder, Adapter.

⚔️ **Security Issues Examples:**
- Hardcoded credentials.
- Unencrypted API calls.
- Unsanitized user input.
- Lack of error handling exposing stack traces.
- Storing sensitive data in plain text.

🏗️ **Architecture Suggestions:**
- Identify violations of Clean Architecture or MVVM principles.
- Recommend improved layering, abstraction, or modularization.

Return response strictly as **VALID JSON** (no text, no markdown), with this structure:
{
 "solid_principles": [
    {"title": "", "file": "", "class": "", "explanation": ""}
 ],
 "design_patterns": [
    {"title": "", "file": "", "class": "", "reason": ""}
 ],
 "security_issues": [
    {"title": "", "file": "", "line": "", "details": ""}
 ],
 "architecture": [
    {"title": "", "file": "", "suggestion": "", "benefit": ""}
 ],
 "final_recommendations": [
    {"title": "", "description": ""}
 ]
}
"""

        messages = [
            {"role": "system", "content": "You are a strict JSON-only code reviewer."},
            {"role": "user", "content": prompt + "\n\nProject Summary:\n" + json.dumps(summary_json)[:15000]}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1800
        }

        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=180)

        if response.status_code != 200:
            raise Exception(f"Mistral API Error: {response.text}")

        try:
            text = response.json()["choices"][0]["message"]["content"]
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
        except Exception as e:
            print("⚠️ Raw Response:")
            print(text if 'text' in locals() else response.text)
            raise Exception("Invalid or non-JSON response from Mistral.") from e
