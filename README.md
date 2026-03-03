## Job AI Agent

This project is a small command-line tool that reads a resume in `.docx` format, infers the candidate's top skills using an LLM, searches live job listings with SerpAPI, and picks the best matching role with a short explanation.

### Requirements

- Python 3.10+
- A virtual environment (recommended)
- Anthropic API key
- SerpAPI key

### Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root:

```text
ANTHROPIC_API_KEY=your_anthropic_key_here
SERPAPI_KEY=your_serpapi_key_here
```

### Usage

Run the script from the project root:

```bash
python script.py
```

Then follow the prompts to provide:
- The path to your resume `.docx` file
- Your target role
- Your preferred location

