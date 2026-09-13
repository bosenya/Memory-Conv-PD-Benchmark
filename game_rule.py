from agent import llm_input
from payoff import payoff_text

## -- Rewrite following to functions according to our settings and complete docstring

def tell_game_rule_no_conv(agent, payoff , R, rand_stop):
    """Tell the agent the game rules without a messaging phase."""
    round_info = f"a repeated prisoner's dilemma lasting exactly {R} rounds"
    if rand_stop:
        round_info = f"a repeated prisoner's dilemma where the game may end randomly after each round"
    
    prompt = f"""
You are a rational player playing {round_info} against another independent AI agent. 
In each round, your will choose whether to Cooperate (C) or Defect (D). 
Please use your previous rounds memory to make action decisions.

Payoff matrix: 
{payoff_text(payoff)}

These are the rules for the game.
"""
    return llm_input(agent, prompt)

def tell_game_rule(agent, payoff, R, rand_stop):
    """Tell the agent the game rules with a messaging phase."""
    round_info = f"a repeated prisoner's dilemma lasting exactly {R} rounds"
    if rand_stop:
        round_info = f"a repeated prisoner's dilemma where the game may end randomly after each round"
    
    prompt = f"""
=== GAME RULE ===
You are a rational player playing {round_info} against another independent AI agent. 
The game consists of a messaging phase and an action phase.  
In the messaging phase, you may send a message to the opponent. 
Your message does not necessarily need to be truthful, but can be strategic to affect your opponent's action. 
Then your and opponent's messages are available to both players before making a decision in the action phase. 
Note: 
- The opponent will see your message before making its decision.
- The opponent is not required to follow your suggestion.
- Action space: Cooperate (C) or Defect (D).
- Please use your previous rounds memory to compose messages and make action decisions

Payoff matrix: 
{payoff_text(payoff)}

These are the rules for the game.
"""
    return llm_input(agent, prompt)