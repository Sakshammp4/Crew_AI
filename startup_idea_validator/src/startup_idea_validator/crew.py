from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from dotenv import load_dotenv
import os
load_dotenv()

MODEL = os.getenv("MODEL", "groq/llama-3.3-70b-versatile")

web_search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

toolskit = [web_search_tool, scrape_tool]

@CrewBase
class StartupIdeaValidator():

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"


#========================1_Agent======================

    @agent
    def idea_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["idea_analyst"],
            tools=toolskit,
            llm=LLM(model=MODEL)
        )

#========================2_Agent======================

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_analyst"],
            tools=toolskit,
            llm=LLM(model=MODEL)
        )

#========================3_Agent======================

    @agent
    def customer_insight_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["customer_insight_agent"],
            tools=toolskit,
            llm=LLM(model=MODEL)
        )

#======================== Task======================

    @task
    def idea_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["idea_analysis_task"]
        )

    @task
    def market_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["market_analysis_task"],
            context=[self.idea_analysis_task()]
        )

    @task
    def customer_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["customer_research_task"],
            context=[
                self.idea_analysis_task(), 
                self.market_analysis_task()
            ]
        )

    @task
    def final_decision_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_decision_task"],
            context=[
                self.idea_analysis_task(), 
                self.market_analysis_task(), 
                self.customer_research_task()
            ]
        )
#======================== Crew ======================

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
