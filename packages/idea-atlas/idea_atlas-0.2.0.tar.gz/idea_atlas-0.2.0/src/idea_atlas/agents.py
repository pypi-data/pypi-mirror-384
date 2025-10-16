from textwrap import dedent
from crewai import LLM, Agent

class AtlasAgents:
   """
   Defines reusable, general-purpose agents.

   Methods:
       research_agent: Creates an agent that can search the web based on user configuration.
   """
   def __init__(self, llm: str, web_search_tool, max_iterations: int):
       if not isinstance(llm, str) or not llm:
           raise ValueError("llm must be a non-empty string")
       if not isinstance(max_iterations, int) or max_iterations <= 0 :
           raise ValueError("max_iterations must be a positive integer")      

       self.llm = LLM(model=llm)
      
       self.web_search_tool = web_search_tool
       
       self.max_iterations = max_iterations

   def research_agent(self):
       return Agent(
           role="Web Research Specialist",
            backstory=dedent("""
                You are a highly skilled research analyst known for your ability to find accurate, reliable,
                and relevant information using web search. Your background includes deep experience in 
                sourcing public-sector content, news articles, documentation, datasets, and more.

                You rely heavily on trusted sources, using advanced search techniques and analytical judgment 
                to filter out noise and provide only what matters. You're rigorous, fact-based, and avoid guessing.
            """),
            goal=dedent("""
                Conduct high-quality research on the internet using trusted sources. 
                Filter irrelevant or duplicate information and ensure only reliable, verifiable results are returned.
            """),
           tools=[self.web_search_tool],
           allow_delegation=False,
           llm=self.llm,
           max_iter=self.max_iterations
       )
