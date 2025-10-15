
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain.schema import SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from datetime import date
from typing import Type
import json
import pandas as pd
from typing import Optional
from sqlalchemy import create_engine

class HRAgent:

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

    def get_agent(self,last_message=None, callback_handler=None,
                  name:str = None,
                  employee_name:str = None,
                  companies:list[str] = None,
                  content:str = None):
        name = name
        employee_name = employee_name
        year = date.today().year
        print(f'GET AGENT YEAR={year}')
        companies = companies
        print(f'COMPANIES={companies}')
        content=content
        # if (employee_name != None) and (len(employee_name) > 0):
        #     content +=f"\n5/ You are currently talking about the employee {employee_name}"
        if last_message:
            content +=f"\n5/ The last response you sent was: \"{last_message[1]}\""
        print(content)
        system_message = SystemMessage(content)
        hr_tool = HRRecordsTool(
            path = self.path,
            db_domain=self.db_domain,
            db_port=self.db_port,
            db_name=self.db_name,
            db_password=self.db_password
        )
        leaves_tool = LeavesTool(
            path = self.path,
            db_domain=self.db_domain,
            db_port=self.db_port,
            db_name=self.db_name,
            db_password=self.db_password
        )
        employee_list_tool = EmployeeListTool(
            path = self.path,
            db_domain=self.db_domain,
            db_port=self.db_port,
            db_name=self.db_name,
            db_password=self.db_password
        )

        tools = [
            hr_tool,
            leaves_tool,
            employee_list_tool
        ]

        agent_kwargs = {
            "system_message": system_message,
        }
        llm_ver = self.llm_ver
        if callback_handler != None:
            llm=ChatOpenAI(temperature=self.temperature, model_name=llm_ver, streaming=self.streaming, callbacks=callback_handler)
        else:
            llm = ChatOpenAI(temperature=0, model=llm_ver, verbose=self.verbose)
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.verbose,
            agent_kwargs=agent_kwargs,
        )

        return agent

class HRRecordsInput(BaseModel):
    """Inputs for get_content function"""
    first_name: str = Field(description="The first name of the employee to get records for.")
    last_name: str = Field(description="The last name of the employee to get records for.")
    start_date: date = Field(description="The start date of the entries that you want to query. Set to January 1, 1970 if not specifically asked for a joining date.")
    end_date: date = Field(description="The end date of the entries that you want to query. Set to the end of the current year if not specifically asked for a joining date.")
    

class HRRecordsTool(BaseTool):
    name = "hr_records_tool"
    description = "Use to get information about an employee. Whenever you see a record_url in your result, render it as a link."
    args_schema: Type[BaseModel] = HRRecordsInput
    
    # Make the database fields optional with a default of None
    path: Optional[str] = Field(None, description="The config path")
    db_domain: Optional[str] = Field(None, description="The database domain")
    db_port: Optional[str] = Field("3306", description="The database port")
    db_name: Optional[str] = Field(None, description="The database name")
    db_password: Optional[str] = Field(None, description="The database password")
    #doc: Optional[str] = Field(None, description="The employee doc")
    #emp: Optional[str] = Field(None, description="The emp unique id")

    def get_data(self, first_name=None, last_name=None, start_date=None, end_date=None):

        if start_date == 'None':
            start_date = None
        if end_date == 'None':
            end_date = None
        if len(first_name) > 0:
            first_name = first_name.split()[0]
        if len(last_name) > 0:
            last_name = last_name.split()[-1]
            print(f'{first_name} {last_name} {start_date} {end_date}')
            conn_string = self.get_conn_string()
            db_connection = create_engine(conn_string)
        
            query = """
            SELECT * FROM `tabEmployee`
            WHERE first_name LIKE %s
            AND last_name LIKE %s
            """
            params = (f"{first_name}%", f"{last_name}%")
            try:
                df = pd.read_sql(query, con=db_connection, params=params)

                if not df.empty:
                    df['full_name'] = df['first_name'] +' '+df['last_name']
                    df['record_url'] = df.apply(lambda x: f"/app/employee/{x['name']}", axis=1)
                    return df.to_dict(orient='records')
                else:
                    return "Employee Not Found"
            except Exception as e:
                print(f"Error executing query: {e}")
                return str(e)
        
    def get_conn_string(self):
        path = f'{self.path}/site_config.json'
        with open(path) as file:
            j = json.load(file)
            #print(j)
            conn_string = f'mariadb+pymysql://{j["db_name"]}:{j["db_password"]}@{self.db_domain}:{self.db_port}/{j["db_name"]}'
            #print("conn_string: ", conn_string)
            return conn_string

    def _run(self, first_name: str, last_name: str, start_date: date, end_date : date):
        #return self.get_data(first_name, last_name, start_date, end_date)
        data = self.get_data(first_name, last_name, start_date, end_date)

        if data != "Employee Not Found":
            if data != None:
                print("Employee Data:", data)
                emp = data[0]
                full_name = emp.get('full_name', None)
                print("Employee Full Name:", full_name)
                return {"employee": data, "full_name": full_name}
            else:
                return "No data Found. "
        else:
            #print(data)
            return {"error": data}

    def _arun(self,  first_name: str, last_name: str, attr: str):
        raise NotImplementedError("error here")
    

class LeavesInput(BaseModel):
    """Inputs for get_content function"""
    first_name: str = Field(description="The first name of the employee to get records for.")
    last_name: str = Field(description="The last name of the employee to get records for.")
    start_date: date = Field(description="The start date of the entries that you want to query")
    end_date: date = Field(description="The end date of the entries that you want to query")


class LeavesTool(BaseTool):
    name = "leaves_tool"
    description = "Use to get information about an employee's leaves. Use only if specifically asked about leaves."
    args_schema: Type[BaseModel] = LeavesInput

    # Make the database fields optional with a default of None
    path: Optional[str] = Field(None, description="The config path")
    db_domain: Optional[str] = Field(None, description="The database domain")
    db_port: Optional[str] = Field("3306", description="The database port")
    db_name: Optional[str] = Field(None, description="The database name")
    db_password: Optional[str] = Field(None, description="The database password")


    def get_data(self, first_name, last_name, start_date=None, end_date=None):
        print(f'{first_name} {last_name} {start_date} {end_date}')
        #doc = self.doc
        #print(doc)
        # return "doc"
        conn_string = self.get_conn_string()
        db_connection = create_engine(conn_string)
    
        query = """
        SELECT name FROM `tabEmployee`
        WHERE first_name LIKE %s
        AND last_name LIKE %s
        """
        params = (f"{first_name}%", f"{last_name}%")
        try:
            df = pd.read_sql(query, con=db_connection, params=params)

            if not df.empty:
                name = df['name'][0] 
                print("name: ", name)
                if name:
                    leave_query = """
                    SELECT leave_type, from_date, to_date, status, total_leave_days
                      FROM `tabLeave Application`
                    WHERE employee = %s
                    """
                    leave_params = (name,) 
                    
                    try:
                        leave_df = pd.read_sql(leave_query, con=db_connection, params=leave_params)

                        if not leave_df.empty:

                            return leave_df.to_dict(orient='records')
                        else:
                            return "No Leave details found."
                    except Exception as e:
                        print(f"Error executing query: {e}")
                        return str(e)


                else:
                    return "Employee Not Found"
                
            else:
                return "Employee Not Found"
        except Exception as e:
            print(f"Error executing query: {e}")
            return str(e)

    def get_conn_string(self):
        path = f'{self.path}/site_config.json'
        with open(path) as file:
            j = json.load(file)
            conn_string = f'mariadb+pymysql://{j["db_name"]}:{j["db_password"]}@{self.db_domain}:{self.db_port}/{j["db_name"]}'
            return conn_string

    def _run(self, first_name: str, last_name: str, start_date: date, end_date : date):
        return self.get_data(first_name, last_name, start_date, end_date)

    def _arun(self,  first_name: str, last_name: str, attr: str):
        raise NotImplementedError("error here")


class EmployeeListInput(BaseModel):
    """Inputs for get_content function"""
    company: str = Field(description="The company to get records for. Set to blank to a list for all companies.")
    start_date: date = Field(description="The start date of the entries that you want to query. Set to January 1, 1970 if not specifically asked for a joining date.")
    end_date: date = Field(description="The end date of the entries that you want to query. Set to the end of the current year if not specifically asked for a joining date.")
    status: str = Field(description="The employee status to look for. Possibe values are ['Active', 'Inactive', 'Suspended', 'Left']")
    

class EmployeeListTool(BaseTool):
    name = "employee_list_tool"
    description = "Use to get a list of employees for a company, Always provide full names. When presenting a list, include the record_url rendered as a link."
    args_schema: Type[BaseModel] = EmployeeListInput

    # Make the database fields optional with a default of None
    path: Optional[str] = Field(None, description="The config path")
    db_domain: Optional[str] = Field(None, description="The database domain")
    db_port: Optional[str] = Field("3306", description="The database port")
    db_name: Optional[str] = Field(None, description="The database name")
    db_password: Optional[str] = Field(None, description="The database password")

    def get_data(self, company, start_date=None, end_date=None, status='Active'):
        print(f'{company} {start_date} {end_date}')
        conn_string = self.get_conn_string()
        db_connection = create_engine(conn_string)
        conditions = f" WHERE status = '{status}'"
        if company:
            conditions = f" WHERE company = '{company}'"

        if start_date and start_date != 'None':
            if status == 'Left':
                conditions = f" WHERE relieving_date between '{start_date}' and '{end_date}'"
            else:
                conditions = f" WHERE date_of_joining between '{start_date}' and '{end_date}'"

        sql = f'SELECT name, first_name, last_name, company, status, designation, date_of_joining, relieving_date FROM `tabEmployee` {conditions} '
        print("sql: ", sql)
        df = pd.read_sql(sql, con=db_connection)

        if not df.empty:
            df['full_name'] = df['first_name'] +' '+df['last_name']
            df['record_url'] = df.apply(lambda x: f"/app/employee/{x['name']}", axis=1)
            return df.to_dict(orient='records')
        else:
            return 'No Records Found'

    def get_conn_string(self):
        path = f'{self.path}/site_config.json'
        with open(path) as file:
            j = json.load(file)
            conn_string = f'mariadb+pymysql://{j["db_name"]}:{j["db_password"]}@{self.db_domain}:{self.db_port}/{j["db_name"]}'
            return conn_string

    def _run(self, company: str, start_date: date, end_date : date, status: str):
        return self.get_data(company, start_date, end_date, status)

    def _arun(self,  company: str, attr: str):
        raise NotImplementedError("error here")