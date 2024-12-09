#!/usr/bin/env python
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, listen, start
from tools.tobertos_tools import is_file_outdated
from crews.db_crew.db_crew import SqlQueryBuilder, DatabaseCrew



class DbState(BaseModel):
    """
    State model for the database flow.
    
    Attributes:
        schema_outdated (bool): Flag indicating if the database schema needs updating
        user_question (str): The question asked by the user about the database
        answer (str): The answer retrieved from the database for the user's question
        memory (ChatMemory): The memory object for storing conversation history
    """
    schema_outdated: bool = False
    user_question: str = Field("", description="The user's question about the database")
    answer: str = Field("", description="The answer to the user's question")


class DbFlow(Flow[DbState]):
    """
    Flow for handling database queries and schema management.
    """
    SCHEMA_FILE = "/Users/tobiasmaissen/Desktop/PythonProjects/ChatWithDB/schema.json"
    
    def __init__(self, user_question: str):
        """Initialize the flow with a user question."""
        super().__init__()
        self.state.user_question = user_question
        
    @start()
    def check_schema(self):
        """Check if the schema file needs to be updated."""
        self.state.schema_outdated = is_file_outdated(self.SCHEMA_FILE)
        
    @listen(check_schema)
    def update_schema_if_needed(self):
        """Update the database schema if it's outdated."""
        if self.state.schema_outdated:
            DatabaseCrew().crew().kickoff()
        
    @listen(update_schema_if_needed)
    def answer_question(self):
        """Process the user's question and get an answer from the database."""
        result = SqlQueryBuilder().crew().kickoff(
            inputs={
                "business_requirement": self.state.user_question
            }
        )
        self.state.answer = result.json_dict["final_answer"]

def get_db_answer(question: str) -> str:
    """Main entry point for getting answers from the database."""
    flow = DbFlow(user_question=question)
    flow.kickoff()
    return flow.state.answer


def plot():
    poem_flow = DbFlow()
    poem_flow.plot()


if __name__ == "__main__":
    # Example usage
    # question = "Which customer ID has the largest invoice sum? Tell me the Name and the SUM."
    # question = "And where does she live?"
    
    # question = "Is there a customer with the name Robert in the database?"
    question = "Okay, and what is his revenue?"
    answer = get_db_answer(question)
    print(f"Q: {question}\nA: {answer}")