import json
from pydantic import BaseModel

def llm_response_formatter(response, llm_provider, logger):
    """ Extract message content and send to Agents
    Args:
        response: llm provider response
        llm_provider: llm provider name
    Raises:
        ValueError: when llm provider not matched
    Returns: message content as response
    """
    try:
        logger.info('formatting llm response....')
        
        
        # Handle tuple response
        if isinstance(response, tuple):
            logger.info('llm tuple response formatting...')
            response = response[0]

        # parse the response if it's a JSON string
        if isinstance(response, str):
            logger.info('llm json string response formatting...')
            response = response.strip()

        logger.info('extracting message content from llm response....')
        
        if llm_provider == 'cortex':
            if isinstance(response, BaseModel):
                return response
            return response.strip()

        # Extract response based on llm provider
        if llm_provider == 'anthropic':
            response = response.content[0].text.strip()
        elif llm_provider == 'openai':
            return getattr(response, 'output_parsed', None) or response.output_text
        else:
            raise KeyError(f"Unsupported llm provider: {llm_provider}")

        logger.info(f'formatted response: {response}')
        return response
    except Exception as e:
        logger.error(f"Error while formatting llm response {llm_provider}: {e}")
        raise


def llm_response_formatter_langchain(response, llm_provider, logger):
    """ Extract message content and send to Agents
    Args:
        response: llm provider response
        llm_provider: llm provider name
    Raises:
        ValueError: when llm provider not matched
    Returns: message content as response
    """
    try:
        print("res in formatter: ", response)
        logger.info('formatting llm response....')
        
        # Handle tuple response
        if isinstance(response, tuple):
            logger.info('llm tuple response formatting...')
            response = response[0]

        # parse the response if it's a JSON string
        if isinstance(response, str):
            logger.info('llm json string response formatting...')
            response = json.loads(response)

        logger.info('extracting message content from llm response....')
        
        # Extract response based on llm provider
        if llm_provider == 'cortex' or llm_provider == 'openai':
            print("response:" , response)
            response = response.content.strip()
            # # Add explicit validation for Cortex response structure
            # if 'choices' not in response or not response['choices']:
            #     raise ValueError(f"Invalid response format from llm provider {llm_provider}, response: {response}")
            # response = response['choices'][0]['messages'].strip()
        # elif llm_provider == 'anthropic':
        #     response = response.content[0].text.strip()
        else:
            raise KeyError(f"Unsupported llm provider: {llm_provider}")

        logger.info(f'formatted response: {response}')
        return response
    except Exception as e:
        logger.error(f"Error while formatting llm response {llm_provider}: {e}")
        raise