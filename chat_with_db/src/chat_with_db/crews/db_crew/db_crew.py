from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import NL2SQLTool, JSONSearchTool
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from crewai.memory.entity.entity_memory import EntityMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.memory.storage.rag_storage import RAGStorage

# Load Environment Variables
load_dotenv()

# Define the data directory
DATA_DIR = "./db"

embedder = {
    "provider": "openai",
    "config": {
        "model": "text-embedding-ada-002"
    }
}

# Initialize the Long Term Memory
ltm = LongTermMemory(
    storage=LTMSQLiteStorage(
        db_path=f"{DATA_DIR}/long_term_memory.db")
)

# Initialize the Short Term Memory
stm = ShortTermMemory(
    storage=RAGStorage(
        type="short_term",
        embedder_config=embedder
    )
)

# Initialize the Entity Memory
em = EntityMemory(
    storage=RAGStorage(
        type="entities",
        embedder_config=embedder
    )
)

# Create Tools
nl2sql = NL2SQLTool(db_uri=f'postgresql://tobiasmaissen:{os.getenv("POSTGRESQL_KEY")}@localhost:5432/chinook')


# Define a Pydantic model for output details
class QaDetails(BaseModel):
    """
    Stores the details of a question-answer interaction with the database.
    Used to track the flow from user input to SQL query to final answer.
    """
    user_input: str = Field(..., description="The user's input question")
    sql_queries: str = Field(..., description="The SQL queries to answer the user's question")
    final_answer: str = Field(..., description="The final answer to the user's question")

class TableColumn(BaseModel):
    """
    Represents a single column in a database table.
    Contains metadata about the column including its name, type, and key relationships.
    """
    name: str  # Name of the column
    data_type: str  # SQL data type (e.g. varchar, integer, etc)
    is_primary: bool  # Whether this column is a primary key
    foreign_key: Optional[str] = None  # Reference to another table if this is a foreign key
    description: Optional[str] = None  # Human-readable description of the column's purpose

class TableRelation(BaseModel):
    """
    Defines a relationship between two database tables.
    Maps the foreign key relationships and cardinality between tables.
    """
    from_table: str  # Source table name
    to_table: str  # Target table name 
    from_column: str  # Column in source table
    to_column: str  # Column in target table
    relation_type: str  # Type of relationship: "one_to_one", "one_to_many", etc.

class DatabaseSchema(BaseModel):
    """
    Complete representation of a database schema.
    Contains table definitions, relationships between tables, and helpful metadata
    for understanding and querying the database structure.
    """
    tables: Dict[str, List[TableColumn]]  # Map of table names to their columns
    relationships: List[TableRelation]  # List of all table relationships
    common_joins: List[Dict[str, List[str]]]  # Frequently used table join patterns
    table_descriptions: Dict[str, str]  # Human-readable descriptions of each table




# Building the Crew for the database
@CrewBase
class DatabaseCrew():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    SCHEMA_FILE = "schema.json"

    @agent
    def database_investigator(self) -> Agent:
        return Agent(
            config=self.agents_config['database_investigator'],
            tools=[nl2sql],
            verbose=True,
            allow_delegation=False,
        )
        
    @task
    def schema_investigation(self) -> Task:
        return Task(
            config=self.tasks_config['schema_investigation'],
            agent=self.database_investigator(),
            output_json=DatabaseSchema,
            output_file=self.SCHEMA_FILE,
        )
        
    @crew
    def crew(self) -> Crew:
        """Creates a dynamic crew based on needs"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


# Building the Crew for the SQL queries
@CrewBase
class SqlQueryBuilder():
    """SqlQueryBuilder crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    SCHEMA_FILE = "schema.json"

    @agent
    def sql_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['sql_agent'],
            verbose=True,
            tools=[
                nl2sql,
                JSONSearchTool(json_path=self.SCHEMA_FILE)
            ],
            allow_delegation=True
        )
  
    @task
    def sql_construction_task(self) -> Task:
        return Task(
            config=self.tasks_config['sql_construction_task'],
            agent=self.sql_agent(),
            output_json=QaDetails,
            output_file='qa_details.json',
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            long_term_memory=ltm,
            short_term_memory=stm,
            entity_memory=em
        )
