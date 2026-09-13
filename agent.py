from openai import OpenAI
from dotenv import load_dotenv
import os

class Agent:
    def __init__(self, id, model, key):
        self.id = id
        self.model = model
        self.client = OpenAI(api_key = key)

load_dotenv()  ## Load Key from Environment
def get_key(API_key):
    key = os.getenv(API_key)
    if key is None:
        raise ValueError(f"KEY FAILED: {API_key}")
    return key

def llm_input(agent, prompt):
    """
    Send a prompt to the LLM using the agent's previous response as context.
    The function retrieves the agent's model, API client, and ID, then sends
    the current prompt through the Responses API. The previous response is
    provided as conversation context so the LLM can maintain continuity
    across rounds. After receiving the response, its ID is stored in memory
    for use in the next round.

    Args:
        agent: (object) Agent object containing the ID, model, and client.
        prompt: (str) The prompt for the current round.

    Returns: (str) The LLM's response.
    """
    
    model = agent.model
    client = agent.client
    agent_id = agent.id

    ## Send the current round's prompt using the previous response as the conversation context.
    response = client.responses.create(model = model, input = prompt, 
                                       previous_response_id = get_previous_response(agent_id))

    ## Update memory so that the next round can continue from this response.
    set_previous_response(agent_id, response.id)

    return response.output_text.strip()



####################
## MEMORY SECTION ##

## MEMORY STORAGE

previous_response_ids = {}
initialized_agents = {}

## INITIALIZE MEMORY

def initialize_memory(agent_ids):
    global previous_response_ids, initialized_agents
    previous_response_ids = {agent_id: None for agent_id in agent_ids}
    initialized_agents = {agent_id: False for agent_id in agent_ids}

## INITIALIZATION FLAG

def is_initialized(agent_id):
    return initialized_agents.get(agent_id, False)

def set_initialized(agent_id, value = True):
    initialized_agents[agent_id] = value

## RESPONSE MEMORY

def get_previous_response(agent_id):
    return previous_response_ids.get(agent_id)

def set_previous_response(agent_id, response_id):
    previous_response_ids[agent_id] = response_id

## RESET

def reset_memory():
    global previous_response_ids, initialized_agents
    previous_response_ids.clear()
    initialized_agents.clear()