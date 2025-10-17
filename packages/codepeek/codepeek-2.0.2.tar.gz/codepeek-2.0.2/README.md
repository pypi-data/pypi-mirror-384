# 🚀 CodePeek 2.0  
**AI-Powered Codebase Analyzer & Summarizer**  

CodePeek helps you understand any codebase — local or from GitHub — using **AI analysis**.  
It extracts structure, reviews SOLID violations, suggests Design Patterns,  
detects security issues, and exports a clean **PDF report**.

---

## 🌟 Features

✅ Analyze any **local project** or **GitHub repository**  
✅ Detect **SOLID principle violations**  
✅ Recommend **Design Patterns**  
✅ Find **Security & Architecture issues**  
✅ Generate a professional **PDF report**  
✅ Powered by **Mistral AI** (fast, free-tier support)

---

## 🧠 How It Works
1. Extracts your code structure and reads all source files.  
2. Summarizes each file intelligently.  
3. Sends the summary to an AI model for deep code review.  
4. Generates a full visual PDF report with categorized findings.

---

## 🛠️ Installation

```bash
pip install codepeek
```

> Requires Python **3.8+**

---

## ⚙️ Setup

Create a `.env` file in your project root with your **Mistral API key**:
```
MISTRAL_API_KEY=your_api_key_here
```

If you don’t have one yet, get it from [https://console.mistral.ai](https://console.mistral.ai)

---

## 💡 Usage

### 🔍 Analyze a Local Project
```bash
codepeek analyze -p "C:\path\to\project"
```

### 🌐 Analyze a GitHub Repository
```bash
codepeek analyze-github https://github.com/user/repo
```

### 🧾 Summarize (Extract Only)
```bash
codepeek summarize https://github.com/user/repo output.txt
```

---

## 📄 Output Example

After analysis, you’ll get:
- A **PDF report** → `projectname_report.pdf`
- With structured sections like:
  - **SOLID Principles**
  - **Design Patterns**
  - **Security Issues**
  - **Architecture Recommendations**
  - **Final Recommendations**

---

## 🧰 Dependencies

- `requests`  
- `reportlab`  
- `python-dotenv`  
- `tqdm`  

---

## 🧑‍💻 Author

**Ahmed Abd Alzeez**  
[GitHub](https://github.com/Ahmedabdalaziz) • [Email](mailto:ahmedabdalziz.1886@gmail.com)

---

## 📜 License

**MIT License © 2025 Ahmed Abd Alzeez**
