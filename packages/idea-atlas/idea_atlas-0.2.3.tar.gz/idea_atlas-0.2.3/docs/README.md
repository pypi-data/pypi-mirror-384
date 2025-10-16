# gds-idea-atlas
✨ Let Atlas carry your AI workflows ✨

Atlas is a suite of standalone AI agents powered by crewai you can plug into your workflows.
Each agent is designed to perform a focused task well, and can be used either on its own or as part of a larger crew or automation pipeline.

The first available agent is the Researcher.

💡 Use Cases

* Information Gathering → Expand a query into reliable sources and discover material you might have missed.

* Summarization & Synthesis → Turn multiple sources into a concise Markdown or JSON summary.

* Academic & Technical Research → Pull structured insights from research papers and technical documents.

* Workflow Automation → Feed structured results into pipelines, dashboards, or agent frameworks.

* Business & Product Use → Scan markets, competitors, or reviews and generate quick decision-support reports.

📦 Outputs

* Structured JSON validated with Pydantic

* Markdown Summaries for human-readable reports

🔧 Installation

Clone this repository and install dependencies in your preferred environment (e.g. uv, pip, or poetry):

``` 
pip install idea-atlas

or 

uv add idea-atlas
```


You’ll need Python 3.11+.

⚙️ Configuration

Create a .env file at the project root. Add the model and API keys you want to use:

``` MODEL=bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION_NAME=your-aws-region-name
SERPER_AI_KEY=your-serper-api-key 
```
