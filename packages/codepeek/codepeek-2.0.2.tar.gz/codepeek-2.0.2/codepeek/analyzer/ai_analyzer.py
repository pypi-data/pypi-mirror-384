import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


class AIAnalyzer:
    def __init__(self):
        # ✅ حاول تحميل المفتاح من .env أو البيئة
        self.api_key = os.getenv("MISTRAL_API_KEY")

        # ✅ لو مفيش مفتاح، اطلبه من المستخدم أول مرة فقط
        if not self.api_key:
            print("\n════════════════════════════════════════")
            print("🚀 Welcome to CodePeek 2.0")
            print("════════════════════════════════════════\n")
            print("👋 Hello! Let's set up your Mistral AI API key.\n")
            self.api_key = input("🔑 Enter your MISTRAL_API_KEY: ").strip()

            # حفظ المفتاح في .env للاستخدام المستقبلي
            with open(".env", "w") as env_file:
                env_file.write(f"MISTRAL_API_KEY={self.api_key}\n")
            print("\n✅ API key saved successfully! 🎯\n")

        # ✅ اختيار موديل متوافق مع المجاني
        self.model = "open-mistral-7b"
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_recommendations(self, summary_json: dict):
        print("🧠 Sending project summary to Mistral for analysis...\n")

        prompt = """
You are a **Senior Software Architect & Code Reviewer** specializing in Flutter, Android, iOS, frontend, backend, AI, and Clean Architecture.

Your job is to perform an in-depth technical review of this project summary.

🔍 **Goals:**
- Detect violations of the SOLID principles and explain why each one is a violation.
- Detect design patterns used or missing, and recommend better alternatives where applicable.
- Identify security issues (hardcoded secrets, weak validation, unsafe state management, data exposure, insecure API handling, etc.).
- Evaluate architecture quality — separation of layers, dependency flow, state management, reusability, and scalability.
- Provide final recommendations for maintainability, testability, and performance.

🚫 **Ignore Completely:**
- Auto-generated code, build/, .dart_tool/, node_modules/, .gradle/, .idea/, etc.
- Assets, fonts, images, icons, JSONs, or environment files that don't contain logic.

✅ **Focus On:**
- Files under lib/, src/, core/, app/, data/, domain/, presentation/, etc.
- Service classes, repositories, ViewModels, widgets, and their architecture interactions.

🧱 **SOLID Check Examples:**
- SRP: Class handles multiple responsibilities.
- OCP: Hardcoded logic instead of extendable design.
- LSP: Derived widget breaking base behavior.
- ISP: Fat interfaces or large service contracts.
- DIP: UI directly calling repositories or APIs.

🧩 **Design Pattern Examples:**
Factory, Singleton, Strategy, Observer, Repository, Provider, Command, MVC/MVVM, Builder, Adapter, Facade, Decorator.

⚔️ **Security Issues Examples:**
- Hardcoded credentials.
- Unencrypted API calls.
- Unsanitized user input.
- Exposed stack traces.
- Storing sensitive data in plain text.

🏗️ **Architecture Suggestions:**
- Identify Clean Architecture or MVVM violations.
- Suggest improved layering, modularization, and scalability.

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

        # ============================
        # إعداد الرسائل للـ Chat API
        # ============================
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

        # ============================
        # إرسال الطلب إلى API
        # ============================
        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=180)

        # ✅ طباعة رد السيرفر لو حصل خطأ
        if response.status_code != 200:
            print("⚠️ Mistral Response:", response.status_code, response.text)
            raise Exception(f"Mistral API Error: {response.text}")

        # ============================
        # محاولة تحليل الرد JSON
        # ============================
        try:
            text = response.json()["choices"][0]["message"]["content"]
            start = text.find("{")
            end = text.rfind("}") + 1
            parsed = json.loads(text[start:end])
            print("✅ AI analysis completed successfully!\n")
            return parsed

        except Exception as e:
            print("⚠️ Raw Response:")
            print(response.text if response.text else "Empty response from Mistral.")
            raise Exception("Invalid or non-JSON response from Mistral.") from e
