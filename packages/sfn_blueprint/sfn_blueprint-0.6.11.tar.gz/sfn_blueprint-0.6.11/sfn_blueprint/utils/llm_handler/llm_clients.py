import os
from sfn_llm_client.llm_api_client.anthropic_client import AnthropicClient
from sfn_llm_client.llm_api_client.base_llm_api_client import LLMAPIClientConfig
from sfn_blueprint.utils.logging import setup_logger
from sfn_llm_client.llm_api_client.openai_client import OpenAIClient
from snowflake.snowpark import Session
from sfn_llm_client.llm_api_client.cortex_client import CortexClient
from sfn_llm_client.llm_api_client.openai_langchain_client import OpenAILangchainClient
from sfn_llm_client.llm_api_client.cortex_langchain_client import CortexLangchainClient
from urllib.parse import urlparse, parse_qs, unquote
def sfn_openai_client(model):
    logger, _ = setup_logger('sfn_openai_client')
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    try:
        openai_client = OpenAIClient(LLMAPIClientConfig(
            api_key=OPENAI_API_KEY,
            default_model=model,
            headers={}
        ))
        return openai_client
    except Exception as e:
        logger.error(f"Error in OpenAI llm_client creation: {e}")
        raise e

def sfn_anthropic_client(model):
    logger, _ = setup_logger('sfn_anthropic_client')
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    try:
        anthropic_client = AnthropicClient(LLMAPIClientConfig(
            api_key=ANTHROPIC_API_KEY,
            default_model=model,
            headers={}
        ))
        return anthropic_client
    except Exception as e:
        logger.error(f"Error in anthropic llm_client creation: {e}")
        raise e

def sfn_cortex_client(model):
    cortex_client = CortexClient()
    return cortex_client

def sfn_openai_client_langchain(model):
    logger, _ = setup_logger('sfn_openai_client_langchain')
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    try:
        openai_langchain_client = OpenAILangchainClient(LLMAPIClientConfig(
            api_key=OPENAI_API_KEY,
            default_model=model,
            headers={}
        ))
        return openai_langchain_client
    except Exception as e:
        logger.error(f"Error in OpenAI langchain llm_client creation: {e}")
        raise e

def sfn_cortex_client_langchain(model):
    logger, _ = setup_logger('sfn_cortex_client_langchain')

    try:
        cortex_langchain_client = CortexLangchainClient()
        return cortex_langchain_client
    except Exception as e:
        logger.error(f"Error in cortex langchain llm_client creation: {e}")
        raise e
    
# this function takes a jdbc url and extracts the connection parameters
# account,user,password,hostname,schema
def fetch_connection_params(jdbc_url):
    parsed_url = urlparse(jdbc_url)
    user_info, account = parsed_url.netloc.split("@")
    user, password = user_info.split(":")
    account_name = account.split("/")[0]
    password = unquote(password)

    path_parts = parsed_url.path.lstrip("/").split("/")
    database = path_parts[0] if len(path_parts) > 0 else ""
    
    query_params = parse_qs(parsed_url.query)
    warehouse = query_params.get("warehouse", [""])[0]
    schema=query_params.get("schema", [""])[0]
      
    conn= {
        "account": account_name,
        "warehouse": warehouse,
        "database": f"{database}",
        "schema": f"{schema}",
        "user": f"{user}",
        "password": f"{password}"
    }
    print(conn)
    
    return conn

def get_snowflake_session(db_url=None):
    print("inside get_snowflake_session method",db_url)
    # if provided, use the jdbc url- snowflake db url
    db_engine= os.getenv("DB_ENGINE")

    if db_url and db_engine != "snowpark":  
        # Connect to Snowflake
        connection_params=fetch_connection_params(db_url)
        return Session.builder.configs(connection_params).create()
    else:
        # Load environment variables
        db_password = os.getenv("SNOWFLAKE_PASSWORD")
        creds = dict()
        creds["account"] = os.getenv("SNOWFLAKE_ACCOUNT")
        creds["warehouse"] = os.getenv("SNOWFLAKE_WAREHOUSE")
        creds["database"] = os.getenv("SNOWFLAKE_DATABASE")
        creds["schema"] = os.getenv("SNOWFLAKE_SCHEMA")
        
        # Check if any required Snowflake credentials are missing
        required_creds = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA"]
        missing_creds = [cred for cred in required_creds if not os.getenv(cred)]

        if missing_creds:
            raise ValueError(f"Missing Snowflake credentials: {', '.join(missing_creds)}. Please set them in the environment variables or in .env file.")
        
        if db_password:
            creds["password"] = db_password
            creds["user"] = os.getenv("SNOWFLAKE_USER")
            if not creds["user"]:
                raise ValueError("SNOWFLAKE_USER is missing. Please add the Snowflake user credentials.")
        else:
            creds["host"] = os.getenv("SNOWFLAKE_HOST")
            creds["authenticator"] = "oauth"
            try:
                with open("/snowflake/session/token", "r") as token_file:
                    creds["token"] = token_file.read().strip()
            except FileNotFoundError:
                raise FileNotFoundError("Snowflake OAuth token file not found at /snowflake/session/token. Please ensure the token is available.")
        
        try:
            session = Session.builder.configs(creds).create()
            return session
        except Exception as e:
            raise ConnectionError(f"Failed to create Snowflake session: {e}")
