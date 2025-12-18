
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM

from dotenv import load_dotenv
load_dotenv()

# Define LLM configurations
gpt4o = LLM(model="openai/o3-mini-2025-01-31")
claude3 = LLM(model="anthropic/claude-3-5-haiku-20241022")
gemini2 = LLM(model="gemini/gemini-2.0-flash-lite")


# @CrewBase
# class LlmCouncil():
#     """LlmCouncil crew"""

#     agents_config = 'config/agents.yaml'
#     tasks_config = 'config/tasks.yaml'

#     # -------------------
#     # AGENTS
#     # -------------------
#     @agent
#     def gpt_delegate(self) -> Agent:
#         return Agent(
#             config=self.agents_config["gpt_delegate"],
#             llm=gpt4o,
#             verbose=True
#         )

#     @agent
#     def claude_delegate(self) -> Agent:
#         return Agent(
#             config=self.agents_config["claude_delegate"],
#             llm=claude3,
#             verbose=True
#         )

#     @agent
#     def gemini_delegate(self) -> Agent:
#         return Agent(
#             config=self.agents_config["gemini_delegate"],
#             llm=gemini2,
#             verbose=True
#         )

#     @agent
#     def chairman(self) -> Agent:
#         return Agent(
#             config=self.agents_config["chairman"],
#             llm=gpt4o,
#             verbose=True
#         )

#     # -------------------
#     # TASKS (Phase 1: Drafting)
#     # -------------------
#     # We reuse the same config ('gather_answers') but create distinct tasks for each agent
#     # We set async_execution=True so they run in parallel.
    
#     @task
#     def gpt_gather(self) -> Task:
#         return Task(
#             config=self.tasks_config["gather_answers"],
#             agent=self.gpt_delegate(),
#             async_execution=True
#         )

#     @task
#     def claude_gather(self) -> Task:
#         return Task(
#             config=self.tasks_config["gather_answers"],
#             agent=self.claude_delegate(),
#             async_execution=True
#         )

#     @task
#     def gemini_gather(self) -> Task:
#         return Task(
#             config=self.tasks_config["gather_answers"],
#             agent=self.gemini_delegate(),
#             async_execution=True
#         )

#     # -------------------
#     # TASKS (Phase 2: Critiquing)
#     # -------------------
#     # REMOVED async_execution=True here. 
#     # These must be synchronous to properly await the results of the async gather tasks.
    
#     @task
#     def gpt_critique(self) -> Task:
#         return Task(
#             config=self.tasks_config["critique_answers"],
#             agent=self.gpt_delegate(),
#             context=[self.gpt_gather(), self.claude_gather(), self.gemini_gather()],
#         )

#     @task
#     def claude_critique(self) -> Task:
#         return Task(
#             config=self.tasks_config["critique_answers"],
#             agent=self.claude_delegate(),
#             context=[self.gpt_gather(), self.claude_gather(), self.gemini_gather()],
#         )

#     @task
#     def gemini_critique(self) -> Task:
#         return Task(
#             config=self.tasks_config["critique_answers"],
#             agent=self.gemini_delegate(),
#             context=[self.gpt_gather(), self.claude_gather(), self.gemini_gather()],
#         )

#     # -------------------
#     # TASKS (Phase 3: Verdict)
#     # -------------------

#     @task
#     def final_answer(self) -> Task:
#         return Task(
#             config=self.tasks_config["final_answer"],
#             agent=self.chairman(),
#             context=[self.gpt_critique(), self.claude_critique(), self.gemini_critique()]
#         )

#     # -------------------
#     # CREW FLOW
#     # -------------------
#     @crew
#     def crew(self) -> Crew:
#         return Crew(
#             agents=[
#                 self.gpt_delegate(),
#                 self.claude_delegate(),
#                 self.gemini_delegate(),
#                 self.chairman(),
#             ],
#             # Standard CrewAI Sequence:
#             # 1. The 'gather' tasks run first. (Because they are async, they run parallel).
#             # 2. The 'critique' tasks run next. (Because they are sync and have context, they wait for gather to finish).
#             # 3. The 'final' task runs last.
#             tasks=[
#                 self.gpt_gather(),
#                 self.claude_gather(),
#                 self.gemini_gather(),
#                 self.gpt_critique(),
#                 self.claude_critique(),
#                 self.gemini_critique(),
#                 self.final_answer()
#             ],
#             process=Process.sequential,
#             verbose=True,
#         )

@CrewBase
class LlmCouncil():
    """LlmCouncil crew - Optimized for token efficiency"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # -------------------
    # AGENTS
    # -------------------
    @agent
    def gpt_delegate(self) -> Agent:
        return Agent(
            config=self.agents_config["gpt_delegate"],
            llm=gpt4o,
            verbose=True
        )

    @agent
    def claude_delegate(self) -> Agent:
        return Agent(
            config=self.agents_config["claude_delegate"],
            llm=claude3,
            verbose=True
        )

    @agent
    def gemini_delegate(self) -> Agent:
        return Agent(
            config=self.agents_config["gemini_delegate"],
            llm=gemini2,
            verbose=True
        )

    @agent
    def chairman(self) -> Agent:
        return Agent(
            config=self.agents_config["chairman"],
            llm=gpt4o,
            verbose=True
        )

    # -------------------
    # TASKS (Phase 1: Drafting)
    # -------------------
    @task
    def gpt_gather(self) -> Task:
        return Task(
            config=self.tasks_config["gather_answers"],
            agent=self.gpt_delegate(),
            async_execution=True
        )

    @task
    def claude_gather(self) -> Task:
        return Task(
            config=self.tasks_config["gather_answers"],
            agent=self.claude_delegate(),
            async_execution=True
        )

    @task
    def gemini_gather(self) -> Task:
        return Task(
            config=self.tasks_config["gather_answers"],
            agent=self.gemini_delegate(),
            async_execution=True
        )

    # -------------------
    # TASKS (Phase 2: Cross-Critiquing)
    # -------------------
    # KEY OPTIMIZATION: Each model only critiques OTHER models' answers
    # This reduces context by ~33% per critique task
    
    @task
    def gpt_critique(self) -> Task:
        return Task(
            config=self.tasks_config["critique_answers"],
            agent=self.gpt_delegate(),
            # GPT only sees Claude and Gemini answers (not its own)
            context=[self.claude_gather(), self.gemini_gather()],
        )

    @task
    def claude_critique(self) -> Task:
        return Task(
            config=self.tasks_config["critique_answers"],
            agent=self.claude_delegate(),
            # Claude only sees GPT and Gemini answers (not its own)
            context=[self.gpt_gather(), self.gemini_gather()],
        )

    @task
    def gemini_critique(self) -> Task:
        return Task(
            config=self.tasks_config["critique_answers"],
            agent=self.gemini_delegate(),
            # Gemini only sees GPT and Claude answers (not its own)
            context=[self.gpt_gather(), self.claude_gather()],
        )

    # -------------------
    # TASKS (Phase 3: Synthesis)
    # -------------------
    @task
    def final_answer(self) -> Task:
        return Task(
            config=self.tasks_config["final_answer"],
            agent=self.chairman(),
            context=[self.gpt_critique(), self.claude_critique(), self.gemini_critique()]
        )

    # -------------------
    # CREW FLOW
    # -------------------
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.gpt_delegate(),
                self.claude_delegate(),
                self.gemini_delegate(),
                self.chairman(),
            ],
            tasks=[
                self.gpt_gather(),
                self.claude_gather(),
                self.gemini_gather(),
                self.gpt_critique(),
                self.claude_critique(),
                self.gemini_critique(),
                self.final_answer()
            ],
            process=Process.sequential,
            verbose=True,
        )
