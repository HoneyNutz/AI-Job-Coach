# 🤖 AI Job Coach

## Overview

The AI Job Coach is a sophisticated, end-to-end Streamlit application designed to streamline and enhance the job application process. It leverages the power of Large Language Models (LLMs) to provide a suite of tools for job seekers, from initial analysis to the generation of highly personalized and professionally formatted application documents.

This tool transforms the tedious process of tailoring a resume for each job application into a strategic, data-driven, and efficient workflow.

## ✨ Key Features

1.  **Persistent & Personalized Setup**:
    *   **One-Time Setup**: On first launch, the application prompts you to upload your baseline JSON resume and a signature graphic.
    *   **Automatic Asset Loading**: These assets are saved locally, and on subsequent launches, the app loads them automatically, taking you directly to the main workflow.

2.  **Intelligent Job Description Parsing**:
    *   Simply provide a URL or paste the text of a job description.
    *   The AI agent meticulously parses the text, extracting key details like responsibilities, qualifications, and skills into a structured format.

3.  **AI-Powered Resume Optimization Blueprint**:
    *   This is the core feature of the application. The AI acts as an expert career strategist, generating a comprehensive, multi-part blueprint for tailoring your resume to the specific job description.
    *   **Strategic Assessment**: Provides a "Keyword Alignment Score," an overall fitness verdict, and identifies key opportunity areas.
    *   **Modern Keyword Analysis**: Displays a dynamic table of the most important keywords, their status (found/missing), priority, and a confidence score visualized with a progress bar.
    *   **Automated Content Rewriting**: The AI rewrites your professional summary and key achievement bullet points using the STAR-D (Situation, Task, Action, Result, Detail) method for maximum impact.

4.  **Live Resume Editor**:
    *   After reviewing the AI's recommendations, you can edit your resume directly in a live JSON editor within the application.

5.  **Automated Document Generation**:
    *   **Typst Integration**: The application uses the modern, powerful `Typst` typesetting system to generate professional-grade PDF documents.
    *   **One-Click PDF Generation**: With a single click, you can generate a beautifully formatted PDF of your newly optimized resume and a personalized cover letter.
    *   **AI Cover Letter Crafting**: The AI can also generate a tailored cover letter, researching the company and highlighting your most relevant skills.

## 🛠️ Tech Stack

*   **Frontend**: [Streamlit](https://streamlit.io/)
*   **AI/LLM Integration**: [OpenAI API](https://openai.com/)
*   **PDF Generation**: [Typst](https://typst.app/)
*   **Data Validation**: [Pydantic](https://docs.pydantic.dev/)
*   **Core Language**: Python

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   An OpenAI API Key
*   [Typst](https://github.com/typst/typst) installed and available in your system's PATH.
*   [GitHub CLI](https://cli.github.com/) (`gh`) for the initial setup.

### Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/<YOUR_USERNAME>/AI-Job-Coach.git
    cd AI-Job-Coach
    ```

2.  **Set up a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set your OpenAI API Key**:
    *   You can set it as an environment variable:
        ```bash
        export OPENAI_API_KEY="your-api-key-here"
        ```
    *   Or, you can enter it directly into the application's sidebar when you run it.

### Running the Application

1.  **Launch the Streamlit app**:
    ```bash
    streamlit run career_toolkit/app.py
    ```

2.  **First-Time Setup**: On your first run, the app will guide you through uploading your baseline JSON resume (in the [JSON Resume](https://jsonresume.org/schema/) format) and a signature image.

3.  **Start Analyzing**: After the initial setup, you'll be taken directly to the job description entry screen, and you can begin your strategic job application process!
