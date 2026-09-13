import random
from agent import llm_input

## -- TO DOs -- ##
## 1. Review and complete docstring for each function
## 2. complete belief elicitation function and its function calls in match()


def get_payoff(action0: int, action1: int, payoff):
    """Docstring: Return the payoffs for the given pair of actions."""
    return payoff.get_payoff(action0, action1)

def cd_decode(num):
    """Docstring: Convert an encoded action to 'C' or 'D'."""
    if num == 0: return "C"
    if num == 1: return "D"

def action_encode(text):
    """Docstring: Convert an LLM action response to an encoded action."""
    t = text.strip().lower()
    if t.startswith("defect"): return 1
    if t.startswith("cooperate"): return 0
    if t == "cooperate": return 0
    if t == "defect": return 1
    if "defect" in t: return 1
    if "cooperate" in t: return 0
    if t == "c": return 0
    if t == "d": return 1
    return 0  # default is cooperate

def message_request(agent, r, R, rand_stop):
    """Docstring: Request a message from the agent for the current round."""
    round_info = f"Round {r} out of {R} -- Messaging Phase."
    if rand_stop:
        round_info = f"Round {r} Messaging Phase, the game may end randomly after this round."

    prompt = f"""
    {round_info}
    Now is the messaging phase, compose a message to the opponent in at most 50 words.
    """
    return llm_input(agent, prompt)

def belief_elicitation(agent, ):
    raise NotImplementedError

def action_request(agent, r, R, rand_stop):
    """Docstring: Request an action from the agent after the messaging phase."""
    round_info = f"Round {r} out of {R} -- Action Phase."
    if rand_stop:
        round_info = f"Round {r} Action Phase, the game may end randomly after this round."
        
    prompt = f"""
    {round_info}
    Respond with EXACTLY ONE WORD: \"Cooperate\" or \"Defect\" and nothing else.
    """
    return llm_input(agent, prompt)

def action_request_no_conv(agent, r, R, rand_stop):
    """Docstring: Request an action from the agent without a messaging phase."""
    round_info = f"Round {r} out of {R}."
    if rand_stop:
        round_info = f"Round {r}, the game may end randomly after this round."
    
    prompt = f"""
    {round_info} 
    Respond with EXACTLY ONE WORD: \"Cooperate\" or \"Defect\" and nothing else.
    """
    return llm_input(agent, prompt)

def match(P0, P1, conversation, payoff, R, rand_stop = False, stop_prob = 0.1):    
    ## Record all rounds
    history = []

    ## Cumulative payoff
    cumulative_payoff_0 = 0
    cumulative_payoff_1 = 0
    
    ## Random Stopping Toggle
    max_rounds = 1000000 if rand_stop else R
    
    for r in range(1, max_rounds + 1):
        if conversation:
            ## Request message
            message_0 = message_request(P0, r, R, rand_stop)
            message_1 = message_request(P1, r, R, rand_stop)
            
            ## Belief elicitation
            belief_0 = 
            belief_1 = 
            
            ## Request action
            action_0 = action_encode(action_request(P0, r, R, rand_stop))
            action_1 = action_encode(action_request(P1, r, R, rand_stop))
            payoff_0, payoff_1 = get_payoff(action_0, action_1, payoff)
        else:
            message_0, message_1 = None, None
            
            ## Belief elicitation
            belief_0 = 
            belief_1 = 
            
            ## Request action
            action_0 = action_encode(action_request_no_conv(P0, r, R, rand_stop))
            action_1 = action_encode(action_request_no_conv(P1, r, R, rand_stop))
            payoff_0, payoff_1 = get_payoff(action_0, action_1, payoff)
        
        ## Update total payoff
        cumulative_payoff_0 += payoff_0
        cumulative_payoff_1 += payoff_1

        ## Record
        history.append({
            "round": r,
            "message_0": message_0,
            "message_1": message_1,
            "belief_0": belief_0,
            "belief_1": belief_1,
            "action_0": cd_decode(action_0),
            "action_1": cd_decode(action_1),
            "payoff_0": payoff_0,
            "payoff_1": payoff_1,
            "cumulative_payoff_0": cumulative_payoff_0,
            "cumulative_payoff_1": cumulative_payoff_1,
        })
        
        ## Stopping Check (Geometric)
        if rand_stop and random.random() < stop_prob:
            break
    
    return history