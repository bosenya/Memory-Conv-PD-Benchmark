import os
from agent import Agent, get_key, initialize_memory, reset_memory
from game_rule import tell_game_rule, tell_game_rule_no_conv

###################
## CONTROL PANEL ##
SEED = 42               # Same randomness setting for every model
CONV = True             # Conversation Regime
RAND_STOP = True        # Random stop
R = 8                   # Number of rounds per match
STOP_PROB = 0.125       # Game stopping probability in each round
NUM_EACH_AGENT = 6      # Number of agents created for each model (at least one of this variable and number of types in POOL should be even)

POOL = [
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-5.5"
]

PAYOFF = [
    # settings.PayoffMatrix(R = 2, T = 2.1, P = 0, S = -0.1)       ## Extreme Test
    settings.PayoffMatrix(R = 2, T = 3, P = 0, S = -1),      ## rho = 1.5, nu = 1.5
    settings.PayoffMatrix(R = 2, T = 5, P = 0, S = -1),      ## rho = 2.5, nu = 1.5
    settings.PayoffMatrix(R = 2, T = 10, P = 0, S = -1),     ## rho = 5, nu = 1.5
]

###########################
## Step 1: Create agents ##

agents = []
agent_id = 1
for model in POOL:
    for i in range(NUM_EACH_AGENT):
        agents.append(Agent(agent_id, model, get_key("key")))
        agent_id += 1

for a in agents:
    initialize_memory(a.id)

#############################################
## Step 2: Inform all agents the game rule ##
    
    ## Tell Game Rule
    if conversation:
        tell_game_rule(P0, payoff, R, rand_stop)
        tell_game_rule(P1, payoff, R, rand_stop)
    else:
        tell_game_rule_no_conv(P0, payoff, R, rand_stop)
        tell_game_rule_no_conv(P1, payoff, R, rand_stop)


############################################
## Step 3: Repeat L randomized supergames ##








for a in agents:
    reset_memory(a.id)