from textwrap import dedent
from crewai import Task


class AtlasAgentsTasks:
   """
   Defines tasks associated with the agents.


   Methods:
       research_task: Creates general task for research agent.
   """

   def __init__(self, agent,  domain: str, expected_output:str, context: str = None , output_pydantic = None):

       self.agent = agent
       self.domain = domain
       self.context = context
       self.expected_output = expected_output
       self.output_pydantic = output_pydantic

   def research_task(self):
        description = f"""
        Search the web using SerperDevTool to find reliable, high-quality content related to: {self.domain}.
        """

        if self.context:
            description += f"\n\nFor additional guidance, consider the following context:\n{self.context}"

        if self.output_pydantic:
            return Task(
                description=dedent(description),  
                expected_output=self.expected_output,
                output_pydantic=self.output_pydantic,
                agent=self.agent,
        )
        else:
            return Task(
                description=dedent(description),  
                expected_output=self.expected_output,
                agent=self.agent
        )            
