from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from xursparks.error.main import GenericXursparksException

class NLPAgent:

    def __init__(self, temperature:float = None,
                llm_ver:str = None,
                model:str = None,
                embed_batch_size:int = None,
                streaming:bool = None,
                verbose:bool = None) -> None:
        self.temperature = temperature
        self.llm_ver = llm_ver
        self.model = model
        self.embed_batch_size = embed_batch_size
        self.streaming = streaming
        self.verbose = verbose

    def get_agent(self,
                  callback_handler = None,
                  persist_path:str = None,
                  file_path:str = None,
                  metadata_name:str = None,
                  metadata_desc:list[str] = None,
                  system_context:str = None,
                  return_intermediate_steps:bool = None,
                  handle_parsing_errors:bool = None,
                  max_iterations:int = None):
       
        if metadata_name is None or metadata_name.strip() == '':
            metadata_name = "xurpas_faq"
        if metadata_desc is None or metadata_desc.strip() == '':
            metadata_desc = ["Provides information about Xurpas."
                        "Use a detailed plain text question as input to the tool."]
        if system_context is None or system_context.strip() == '':
            raise GenericXursparksException("Must Provide System Context")
        if return_intermediate_steps is None:
            return_intermediate_steps = True
        if handle_parsing_errors is None:
            handle_parsing_errors = True
        if max_iterations is None:
            max_iterations = 10

        if callback_handler != None:
            print("With callback handler!")
            llm = ChatOpenAI(
                temperature=self.temperature,
                model_name=self.llm_ver,
                streaming=self.streaming,
                callbacks=callback_handler
            )
        else:
            llm = ChatOpenAI(
                temperature=self.temperature,
                model=self.llm_ver,
                verbose=self.verbose,
                streaming=self.streaming
            )

        embed_model = OpenAIEmbedding(
            model=self.model, embed_batch_size=self.embed_batch_size
        )

        Settings.llm = llm
        Settings.embed_model = embed_model

        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=persist_path
            )
            data_index = load_index_from_storage(storage_context)

            index_loaded = True
            print("Index was already created. We just loaded it from the local storage.")
        except:
            index_loaded = False
            print("Index is not present. We need it to create it again.")

        if not index_loaded:
            print("Creating Index..")

            docs = SimpleDirectoryReader(
                file_path
            ).load_data()
            data_index = VectorStoreIndex.from_documents(docs)
            data_index.storage_context.persist(persist_dir=persist_path)

            index_loaded = True

        query_engine = data_index.as_query_engine(similarity_top_k=3)

        query_engine_tools = [
            QueryEngineTool(
                query_engine=query_engine,
                metadata=ToolMetadata(
                    name=metadata_name,
                    description=(
                        metadata_desc
                    ),
                ),
            )
        ]

        converted_tools = [t.to_langchain_tool() for t in query_engine_tools]

        print("No of LlamaIndex Tools:", len(converted_tools))

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_context,
                ),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        agent = create_tool_calling_agent(
            llm=llm,
            tools=converted_tools,
            prompt=prompt
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=converted_tools,
            verbose=self.verbose,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=10
        )

        return agent_executor
    
