# sfn_blueprint

`sfn_blueprint` is a modular framework designed for the rapid development of intelligent agents capable of handling various data-related tasks, such as category identification, code execution, feature suggestion generation, and data analysis. These agents integrate with Large Language Model (LLM) clients to perform AI-based tasks. The framework supports various file formats, API client handling, and configurable prompt management, which can be extended with custom logic.

## Features

### Core Focus:
- **LLM Handler**: A handler designed to route LLM requests to the appropriate provider from a range of supported LLM services.

### Available Agents:
- **Base Agent**: A base class that can be extended by other agents.
- **Code Generator**: Automatically categorizes datasets based on column names.
- **Code Execution**: Dynamically executes code on data frames.
- **Feature Suggestion**: Provides feature engineering suggestions based on datasets.
- **Data Analyzer**: Analyzes datasets and returns detailed statistics.
- **Validation and Retry Agent**: Validates and retries LLM-generated responses by an agent.

## Installation

You can install the `sfn_blueprint` framework via pip:

```bash
pip install sfn_blueprint
```

## Usage

### 0. Environment Setup

To use the agents, you need to specify credentials for your LLM provider. Store the credentials in a `.env` file in your project root directory. Ensure the `python-dotenv` package is installed to load the environment variables.

- For OpenAI, specify the following key in the `.env` file or export these environment variable as per your llm provider selection:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

#### OR

- For Anthropic, specify the following key in the `.env` file:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### OR


#### Snowflake Cortex Environment Configuration

##### ✅ Environment Variables

To connect to **Snowflake Cortex**, configure the following environment variables in your `.env` file based on your authentication method.

---

##### 1️⃣ **For Username/Password Authentication:**
```bash
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

---

##### 2️⃣ **For OAuth Authentication (without password):**
```bash
SNOWFLAKE_HOST=your_hostname
SNOWFLAKE_AUTHENTICATOR=oauth
SNOWFLAKE_TOKEN=your_token
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

> 🔔 **Note:** For OAuth, ensure the OAuth token is accessible at `/snowflake/session/token`.

---

##### ✅ Parameters:
| Name     | Type   | Description                                                         | Default |
|----------|--------|---------------------------------------------------------------------|---------|
| db_url  | string | (Optional) JDBC-style Snowflake connection URL for direct use.     | `None`  |

---

##### ✅ Behavior:
- **If `db_url` is provided**:
  - The function extracts connection parameters from the db_url to create a session, unless it is a Snowpark session, in which case the session is obtained from the environment.
- **If `db_url` is not provided (in case snowflake details must be provided)**:
  - The function loads Snowflake credentials from environment variables.
  - It supports both **username/password** and **OAuth token** authentication.
  - Performs validation to ensure all required environment variables are present.
  - Raises errors if essential credentials are missing or if the OAuth token file is not found.
### Providing a Real Quick User Interface Using SFNBaseView:
The `SFNBaseView` class is a custom view handler to facilitate easy integration of user interface components
for AI Agents. It provides a collection of methods that allow you to build interactive web applications quickly, 
supporting features such as displaying titles, headers, uploading files, and handling progress bars.

#### Key Features:
- Handle file uploads and temporary file storage.
- Display various UI elements such as titles, headers, subheaders, and markdown text.
- Show messages of different types (info, success, error, warning).
- Display data frames, progress bars, and create downloadable files.
- Integrate with radio buttons, select boxes, and more.

To use this component, call its methods to build custom UIs Examples as follows:

##### 1. Display a Title and Header:
```python
from sfnblueprint.views import SFNBaseView

# Initialize the view
view = SFNBaseView(title="Welcome to SFN Base View")

# Display title and headers
view.display_title()  # Displays the title set during initialization
view.display_header("This is the header")
view.display_subheader("This is the subheader")
```

##### 2. Show Messages:
```python
# Show different types of messages
view.show_message("This is an information message.")
view.show_message("This is a success message.", message_type="success")
view.show_message("This is an error message.", message_type="error")
view.show_message("This is a warning message.", message_type="warning")
```

##### 3. File Upload and Handling: 
Upload a file and usinf `save_uploaded_file` save it temporarily to get path of a file,
as this creates a temp_files folder to save the files and create its path, 
you can use `delete_uploaded_file` to later delete temp file 
also don't forget to add temp_files in .gitignore file to ignore temporary file 

```python
uploaded_file = view.file_uploader("Upload a file", accepted_types=["csv"])
if uploaded_file:
    file_path = view.save_uploaded_file(uploaded_file)
    view.show_message(f"File saved at: {file_path}", "success")

    # To delete the uploaded file
    view.delete_uploaded_file(file_path)
```

##### 4. Display DataFrame:
```python
import pandas as pd

# Create a sample DataFrame
data = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35]
})

# Display the DataFrame in the view
view.display_dataframe(data)
```

##### 5. Handle Progress Bars:
```python
# Create a progress bar and update it
progress_bar, status_text = view.create_progress_container()

for progress in range(101):
    view.update_progress(progress_bar, progress / 100)
    status_text.text(f"Progress: {progress}%")
```

##### 6. Radio Button and Select Box:
```python
# Radio Button Example
selected_option = view.radio_select("Choose an option", ["Option 1", "Option 2", "Option 3"])
view.show_message(f"You selected: {selected_option}")

# Select Box Example
selected_item = view.select_box("Choose an item", ["Item A", "Item B", "Item C"])
view.show_message(f"You selected: {selected_item}")
```

### 2. Using the AI Handler

The `SFNAIHandler` helps route LLM requests to different LLM providers, currently supporting OpenAI, Snowflake Cortex, and Anthropic. Below is an example of how to use the `SFNAIHandler` to interact with OpenAI's completion API.

#### Example: Using `SFNAIHandler`

```python
from sfn_blueprint import SFNAIHandler

# Initialize the AI handler
ai_handler = SFNAIHandler()

# Define the prompts and model configuration
system_prompt = "You are an expert assistant."
user_prompt = "What are the categories of this dataset?"
configuration = {
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.7,
    "max_tokens": 100,
    "n": 1,
    "stop": None
}

# Specify the LLM provider (e.g., 'openai') and model
llm_provider = 'openai'
model = 'gpt-4o-mini'

# Process the request using the AI handler
db_url is optional and can be used for cortex
response, token_cost_summary = ai_handler.route_to(llm_provider, model, configuration,db_url=None)
```

The token cost summary will contain the following structure:
- `"prompt_tokens"`: Number of input tokens
- `"completion_tokens"`: Number of output tokens
- `"total_tokens"`: Total tokens used
- `"total_cost_usd"`: Total cost in USD

If the LLM provider is Snowflake Cortex, the token cost summary will include these keys:
- `"prompt_tokens"`: Number of input tokens
- `"completion_tokens"`: Number of output tokens
- `"guardrails_tokens"`: Guardrails tokens
- `"total_tokens"`: Total tokens used
- `"total_cost_in_credits"`: Total cost in credits

### Explanation

1. **Initialize `SFNAIHandler`**: This creates an instance of the handler to route requests to different LLM providers.
2. **Define prompts and configuration**: A system prompt and a user prompt are set, along with other parameters such as `temperature`, `max_tokens`, and `n` (number of responses).
3. **Route the request**: The `route_to()` method sends the request to the specified LLM provider and returns the response.
4. **Extract and print the result**: The response and token cost details are retrieved and displayed.

This example shows how to use the `SFNAIHandler` to easily integrate AI completions into your custom agents. You can modify the prompts and model configurations based on your needs.

---

### 3. Using Agents

### Base Agent with `SFNAgent`

The `SFNAgent` class serves as a foundation for agents performing data-related tasks. It defines the agent's identity through attributes like name and role and provides a structure for executing tasks. Subclasses need to implement the `execute_task` method to perform specific operations on the input data.

#### Example:

```python
from sfn_blueprint import SFNAgent

class YourAgentClass(SFNAgent):
    # Implement custom logic of your agent here
```

### Task with `Task`

The `SFNDataAnalyzerAgent` analyzes DataFrames, generating data summaries. It uses the `Task` class to structure input, including data, task type, and description. The agent processes the data and logs insights such as shape, column types, and missing values. The `Task` class accepts the following parameters:
- `description`: A description of the task.
- `data`: Data to be processed (e.g., DataFrame).
- `path`: The file path for the data.
- `task_type`: Type of task to perform.
- `category`: Category of the task.
- `analysis`: Analysis details (optional).
- `code`: Code related to the task (optional).

#### Example:

```python
from sfn_blueprint import Task
load_task = Task(description="Load the uploaded file", data=uploaded_file, path=file_path)
```

### Validate and Retry Agent with `SFNValidateAndRetryAgent`

The `SFNValidateAndRetryAgent` ensures reliable task execution by validating agent tasks and applying retry logic if validation fails. It retries task execution up to a specified limit and leverages AI models for task validation while logging the progress.

The agent returns the following values:
- **response**: The validated response from the agent.
- **message**: If validation fails, it returns the cause in this message.
- **is_valid**: A boolean (`TRUE/FALSE`) indicating whether the validation was successful.

#### Initialization Parameters:
- **llm_provider**: The name of the LLM provider.
- **for_agent**: The name of the agent for which validation will be applied.

#### Validation Method Parameters (used in `complete()`):
- **agent_to_validate**: The agent instance (e.g., `category_agent`) whose task will be executed.
- **task**: The main task (e.g., `category_task`) for execution.
- **validation_task**: A task (e.g., `validation_task`) that contains the validation context.
- **method_name**: The name of the method (e.g., `execute_task`) to invoke on the agent. This method should be defined within the agent you wish to validate.
- **get_validation_params**: The method (e.g., `get_validation_params`) to retrieve validation-related parameters, which should also be defined within the agent you want to validate.

**Note**: While writing the validation prompt, be sure to append this below statement at the end of validation user prompt:
```bash
"\n- Respond with TRUE on the first line.\nIf any criteria fail, respond with FALSE on the first line followed by a brief reason on the next line."
```

#### Example:

```python
from sfn_blueprint import SFNValidateAndRetryAgent, Task

# Initialize the Validate and Retry Agent
validate_and_retry_agent = SFNValidateAndRetryAgent(
    llm_provider="openai",  # Specify your LLM provider
    for_agent='agent_name'  # The name of the agent to validate
)

# Define your agent and tasks
your_agent_instance = SOMEAgent(llm_provider='openai')
task = Task("Your agent description", data=dataframe)
validation_task = Task("Validate category", data=dataframe)

# Perform the validation with retries
response, message, is_valid = validate_and_retry_agent.complete(
    agent_to_validate=your_agent_instance,
    task=task,
    validation_task=validation_task,
    method_name='main method to execute your agent',
    get_validation_params='method to get validation params',
    max_retries=3,  # Maximum number of retries
    retry_delay=3.0  # Delay between retries in seconds
)
```

### Prompt Manager with `SFNPromptManager`

The `SFNPromptManager` handles and formats prompts for various agent types and LLM providers. It takes the path to a JSON prompt file, loads the configuration, and retrieves formatted system and user prompts for specific tasks.

#### Parameters:
- **agent_type**: The type of agent (e.g., 'feature_suggester').
- **llm_provider**: The name of the LLM provider (e.g., 'openai').
- **prompt_type**: The type of prompt (either 'main' or 'validation').

#### Example:

The JSON prompt configuration file should follow this structure:

```python
{
    "agent_name": {
        "llm_provider_name": {
            "main": {
                "system_prompt": "prompt here...",
                "user_prompt_template": "prompt here..."
            },
            "validation": {
                "system_prompt": "prompt here...",
                "user_prompt_template": "prompt here..."
            }
        }
    }
}
```

Usage example:

```python
from sfn_blueprint import SFNPromptManager

# Initialize the Prompt Manager
prompt_manager = SFNPromptManager(prompt_config_path="path_to_your_json_file")

# Retrieve system and user prompts
system_prompt, user_prompt = prompt_manager.get_prompt(
    agent_type='agent_name', 
    llm_provider='your_llm_provider',
    prompt_type='prompt_type', 
    columns={'key': 'value'}  # Arguments to format the prompt
)
```

### Config Manager with `SFNConfigManager`

The `SFNConfigManager` simplifies the management of configurations by supporting multiple file formats and logging. It allows for easy retrieval of values and supports loading configurations for different environments such as development, staging, and production.

#### Example:

```python
from sfn_blueprint import SFNConfigManager

# Initialize the Config Manager
config_manager = SFNConfigManager(config_path="config/settings.json")

# Retrieve a value from the configuration
db_host = config_manager.get("database.host", default="localhost")
```

---

### Code Executor with `SFNCodeExecutorAgent`

The `SFNCodeExecutorAgent` allows you to execute Python code within a controlled environment, primarily for modifying DataFrames. It accepts a `Task` object that contains the code (`task.code`) and the data (`task.data`), where the data is typically a pandas DataFrame. The `execute_task` method runs the code and returns the modified DataFrame after execution.

#### Example:

```python
from sfn_blueprint import SFNCodeExecutorAgent, Task
import pandas as pd

# Initialize the Code Executor Agent
code_executor = SFNCodeExecutorAgent()

# Create a task with code to modify a DataFrame
task = Task(
    code="df['new_col'] = df['col1'] * 2",
    data=pd.DataFrame({'col1': [1, 2, 3]})
)

# Execute the task and get the modified DataFrame
result_df = code_executor.execute_task(task)
```

### Code Generator with `SFNFeatureCodeGeneratorAgent`

The `execute_task` method in `SFNFeatureCodeGeneratorAgent` generates code using an LLM, cleans it using `clean_generated_code`, and returns the result. It is designed for dynamically creating and cleaning feature-related Python code based on the characteristics of the data, enabling automation in feature engineering or code generation tasks. The method accepts a `Task` object containing data such as suggestions, columns, data types, and sample records.

#### Example:

```python
from sfn_blueprint import SFNFeatureCodeGeneratorAgent

code_generator = SFNFeatureCodeGeneratorAgent(llm_provider='your_llm_provider')

# Sample raw code
raw_code = """
# This is a comment
def my_function():
    print("Hello World")
    return 42
"""

# Clean the generated code
cleaned_code = SFNFeatureCodeGeneratorAgent.clean_generated_code(raw_code)
```

---

### Data Analyzer with `SFNDataAnalyzerAgent`

The `SFNDataAnalyzerAgent` class analyzes a given DataFrame and logs a detailed summary of the data. It extends the `SFNAgent` class and uses the `setup_logger` method for logging.

#### Example:

```python
from sfn_blueprint import SFNDataAnalyzerAgent
from sfn_blueprint import Task

agent = SFNDataAnalyzerAgent()

# Task containing numeric and categorical data
task = Task(
    data=pd.DataFrame({
        'numeric_col': [1, 2, 3, 4, 5],
        'categorical_col': ['A', 'B', 'A', 'B', 'C']
    })
)

# Generate a data summary
summary = agent.execute_task(task)
```

---

### Suggestions Generator with `SFNSuggestionsGeneratorAgent`

The `SFNSuggestionsGeneratorAgent` generates suggestions based on the data provided in a task. It accepts a `Task` object containing a DataFrame (`df`), task type, and category. The agent processes the DataFrame, retrieves prompt configurations, and routes the task to an LLM for suggestions. Parameters include columns, sample records, and statistical descriptions of the data. It is particularly useful for generating insights or suggestions for tasks like feature engineering.

#### Example:

```python
from sfn_blueprint import SFNSuggestionsGeneratorAgent
from sfn_blueprint import Task

suggestions_agent = SFNSuggestionsGeneratorAgent(llm_provider='your_llm_provider')

df = pd.DataFrame()  # Your DataFrame

task = Task(description='some description', data={"df": df}, task_type="test_type", category="test_category")

# Execute the task to get suggestions
suggestions_agent.execute_task(task)
```

---

### Data Loading with `SFNDataLoader`

The `SFNDataLoader` loads data into a pandas DataFrame from various file formats, including CSV, Excel, JSON, and Parquet. It accepts a `Task` object containing the file path and uses the `execute_task` method to determine the file type and load the data via appropriate mapped functions. The `SFNDataLoader` is suitable for dynamically loading data and supports large datasets using Dask for parallel processing. Key parameters include the file path and format, with support for CSV, Excel, JSON, and Parquet files.

#### Example:

```python
from sfn_blueprint import SFNDataLoader, Task

task = Task(description="Load CSV data", data=uploaded_file, path=file_path)

data_loader = SFNDataLoader()

# Load the data into a pandas DataFrame
dataframe = data_loader.execute_task(task)
print(dataframe.head())  # Display the first few rows
```

Note: file path is required to use SFNDataLoader, you can use SFNBaseView to upload file and save it to get path,
also don't forget to add temp_files in .gitignore file to ignore temporary file 
#### Example:

```python
uploaded_file = view.file_uploader("Upload a file", accepted_types=["csv"])
if uploaded_file:
    # To get file path
    file_path = view.save_uploaded_file(uploaded_file)
    view.show_message(f"File saved at: {file_path}", "success")

    # To delete the uploaded temp file
    view.delete_uploaded_file(file_path)
```

## Contact:

For any queries or issues, please contact the maintainer at: `rajesh@stepfunction.ai`