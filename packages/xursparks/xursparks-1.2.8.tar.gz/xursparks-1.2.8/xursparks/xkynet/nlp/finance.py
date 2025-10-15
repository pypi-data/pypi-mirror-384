from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from typing import Type
from langchain.schema import SystemMessage
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from datetime import date
import pandas as pd
import json
from sqlalchemy import create_engine
from typing import Optional

class FinanceAgent:

    def __init__(self, temperature:float = None,
                llm_ver:str = None,
                model:str = None,
                embed_batch_size:int = None,
                streaming:bool = None,
                verbose:bool = None,
                path:str = None,
                db_domain:str = None,
                db_port:str = None,
                db_name:str = None,
                db_password:str = None) -> None:
        self.temperature = temperature
        self.llm_ver = llm_ver
        self.model = model
        self.embed_batch_size = embed_batch_size
        self.streaming = streaming
        self.verbose = verbose
        self.path = path
        self.db_domain = db_domain
        self.db_port = db_port
        self.db_name = db_name
        self.db_password = db_password

    def get_agent(self, doc:list[any],
                  content:str = None):
        year = date.today().year
        print(f'GET AGENT YEAR={year}')
        companies = []
        companies = [x.name for x in doc]
        print(companies)
        system_message = SystemMessage(content)
        accounting_journal_tool = AccountingJournalTool(
            path = self.path,
            db_domain=self.db_domain,
            db_port=self.db_port,
            db_name=self.db_name,
            db_password=self.db_password
        )
        tools = [
            accounting_journal_tool
        ]
        agent_kwargs = {
            "system_message": system_message,
        }
        llm = ChatOpenAI(temperature=self.temperature, model=self.model, verbose=self.verbose)
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.verbose,
            agent_kwargs=agent_kwargs,
        )

        return agent

class AccountingJournalInput(BaseModel):
    """Inputs for get_content function"""
    company: str = Field(
        description="The company that you want to get the journal entries for.")
    start_date: date = Field(
        description="The start date of the journal entries that you want to query")
    end_date: date = Field(
        description="The end date of the journal entries that you want to query")


class AccountingJournalTool(BaseTool):
    name = "accounting_journal_tool"
    description = "Use to get a pandas dataframe of a company's accounting journal entries"
    args_schema: Type[BaseModel] = AccountingJournalInput
    
    # Make the database fields optional with a default of None
    path: Optional[str] = Field(None, description="The config path")
    db_domain: Optional[str] = Field(None, description="The database domain")
    db_port: Optional[str] = Field("3306", description="The database port")
    db_name: Optional[str] = Field(None, description="The database name")
    db_password: Optional[str] = Field(None, description="The database password")



    def get_data(self, company, start_date=None, end_date=None):

        print(f'{company} {start_date} {end_date}')
        conn_string = self.get_conn_string()
        if start_date == None:
            start_date = date(date.today().year, 1, 1)
            end_date = date(date.today().year, 12, 31)
        # print(start_date)
        # print(end_date)
        sql = f'SELECT * FROM `tabJournal Entry` WHERE company="{company}" AND posting_date BETWEEN "{start_date}" AND "{end_date}" ORDER BY posting_date'
        # print (sql)
        db_connection = create_engine(conn_string)
        df = pd.read_sql(sql, con=db_connection)
        print(df.head())
        return df

    def get_conn_string(self):

        print("self.path: ", self.path)
        print("self.db_domain: ", self.db_domain)
        print("self.db_port: ", self.db_port)
        path = f'{self.path}/site_config.json'
        db_domain = self.db_domain
        db_port = self.db_port
        with open(path) as file:
            j = json.load(file)
            #print(j)

            conn_string = f'mariadb+pymysql://{j["db_name"]}:{j["db_password"]}@{db_domain}:{db_port}/{j["db_name"]}'

        #print("conn_string:  ", conn_string)
        return conn_string

    def _run(self, company: str, start_date: date, end_date: date):
        return self.get_data(company, start_date, end_date)

    def _arun(self, cpmpany: str, attr: str):
        raise NotImplementedError("error here")