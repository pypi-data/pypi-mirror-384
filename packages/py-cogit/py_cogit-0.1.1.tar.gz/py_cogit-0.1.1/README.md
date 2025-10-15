

# py-cogit

> Your AI senior software engineer, right in your terminal.

[PyPI Link](https://pypi.org/project/py-cogit/)

`py-cogit` is a command-line tool that acts as your personal code reviewer. It analyzes your staged changes (`git diff --staged`), sends them to Google's AI (Gemini), and provides a detailed analysis on best practices, potential bugs, readability, and even suggests a commit message for you.

Stop committing with `fix: stuff`. Start committing with confidence.

## ✨ Key Features

  - 🤖 **AI-Powered Code Review:** Get insights and suggestions from an AI model trained to act as a senior engineer.
  - 💡 **Structured Analysis:** The output is in JSON format, detailing improvement points, potential risks, and observations per file.
  - commit **Automated Commit Messages:** Generates a commit message suggestion following the [Conventional Commits](https://www.conventionalcommits.org/) standard.
  - ⚙️ **Highly Configurable:** Use the default prompt or completely customize it via a `.env` file.
  - 🔒 **Secure and Local:** Your code is sent directly to the Google API. Your API key remains safe on your local machine.

## 🚀 Installation

Installation is easily done via `pip`.

```bash
pip install py-cogit
```

## 🛠️ Setup

Before using `py-cogit` for the first time, you need to set up your Google API key.

1.  **Get Your API Key:**
    Go to [Google AI Studio](https://aistudio.google.com/) and create your API key.

2.  **Create a `.env` file:**
    In the root of your project (or any parent directory from where you'll run the command), create a file named `.env` and add the following variables.

    ```env
    # .env

    # Your API key from Google AI Studio
    GOOGLE_API_KEY="PASTE_YOUR_API_KEY_HERE"

    # The Gemini model you want to use
    GEMINI_VERSION="gemini-1.5-pro-latest"

    # (Optional) You can override the default prompt here
    PROMPT="You are an AI assistant..."
    ```

## Usage

The workflow is simple and integrates seamlessly with Git.

1.  **Make your code changes** as usual.

2.  **Add your changes** to the Git staging area.

    ```bash
    git add .
    ```

3.  **Run `py-cogit`\!**

    ```bash
    py-cogit
    ```

## 📋 Example Output

After running, `py-cogit` will print a detailed JSON analysis directly to your terminal:

```json
{
  "overall_summary": "This change refactors the script to make the Gemini model version configurable and improves exception handling.",
  "analysis_per_file": [
    {
      "file_name": "main.py",
      "general_observations": [
        "Externalizing the model version to an environment variable is a great practice."
      ],
      "improvement_points": [
        {
          "approximate_line": "22",
          "code_snippet": "model = genai.GenerativeModel(os.getenv(\"GEMINI_VERSION\"))",
          "suggestion": "`os.getenv` will return `None` if the variable is not set, causing an error. Add validation to ensure the variable exists or provide a default value.",
          "category": "Potential Bug",
          "priority": "High"
        }
      ]
    }
  ],
  "potential_risks": [
    "The application now depends on the `GEMINI_VERSION` environment variable. If it is not set, the program will crash."
  ],
  "commit_message_suggestion": {
    "type": "refactor",
    "scope": "main",
    "subject": "configure model version via environment variable"
  }
}
```

## Contributing

Contributions are very welcome\! If you have ideas for new features, improvements, or have found a bug, please open an [Issue](https://github.com/andreisilva1/py-cogit/issues) so we can discuss it.

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.