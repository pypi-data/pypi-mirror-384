from idea_atlas.agents import AtlasAgents
from idea_atlas.tasks import AtlasAgentsTasks
from crewai import Crew


class Research:
    """
    Coordinates research based on the user input.

    Parameters:
        llm (str): The LLM model to use (e.g., "Claude Sonnet 3.7").
        web_search_tool: The search tool instance (e.g., SerperDevTool()).
        max_iterations (int): Max iterations the agent can run.
        domain (str): The topic/subject the agent will research.
        expected_output (str): A clear description of the expected result (e.g JSON, markdown).
        context (str, optional): Additional user-provided context or constraints (e.g list of URLs/documents to extend).
        output_pydantic (Pydantic model, optional): Model to validate the agent's output.
    """

    def __init__(
        self,
        llm: str,
        web_search_tool,
        max_iterations: int,
        domain: str,
        expected_output: str,
        context: str = None,
        output_pydantic = None
    ):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.max_iterations = max_iterations
        self.domain = domain
        self.expected_output = expected_output
        self.context = context
        self.output_pydantic = output_pydantic

    def run(self):
        agent_builder = AtlasAgents(
            llm=self.llm,
            web_search_tool=self.web_search_tool,
            max_iterations=self.max_iterations
        )
        research_agent = agent_builder.research_agent()

        task_builder = AtlasAgentsTasks(
            agent=research_agent,
            domain=self.domain,
            expected_output=self.expected_output,
            context=self.context,
            output_pydantic=self.output_pydantic
        )
        research_task = task_builder.research_task()

        crew = Crew(
            agents=[research_agent],
            tasks=[research_task],
            verbose=True
        )

        result = crew.kickoff()
        return result
