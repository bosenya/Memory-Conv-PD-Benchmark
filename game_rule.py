"""Prompts that initialize the repeated Prisoner's Dilemma rules for an agent."""

from agent import llm_input
from payoff import payoff_text


def _horizon_text(R, rand_stop, stop_prob=None, disclose_stop_prob=False):
    """Return a consistent natural-language description of the game horizon.

    Args:
        R: Number of rounds in a fixed-horizon game.
        rand_stop: Whether the game stops randomly after completed rounds.
        stop_prob: Per-round stopping probability. Required only when it will be
            disclosed to the agent.
        disclose_stop_prob: Whether to reveal ``stop_prob`` and the continuation
            probability to the agent.

    Returns:
        A sentence describing the horizon information available to the agent.

    Raises:
        ValueError: If fixed-round or disclosed-probability settings are invalid.
    """
    if not rand_stop:
        if not isinstance(R, int) or R < 1:
            raise ValueError("R must be a positive integer for a fixed-horizon game.")
        return f"a repeated Prisoner's Dilemma lasting exactly {R} rounds"

    if disclose_stop_prob:
        if stop_prob is None or not 0.0 < stop_prob <= 1.0:
            raise ValueError(
                "A stop_prob in (0, 1] is required when disclosing the probability."
            )
        continuation_prob = 1.0 - stop_prob
        return (
            "a repeated Prisoner's Dilemma that stops independently after each "
            f"completed round with probability {stop_prob:g} and continues with "
            f"probability {continuation_prob:g}"
        )

    return (
        "a repeated Prisoner's Dilemma that may stop independently after each "
        "completed round; the numerical stopping probability is not disclosed"
    )


def _game_rule_prompt(payoff, R, rand_stop, conversation, stop_prob, disclose_stop_prob):
    """Build the common rule prompt for conversation and no-conversation games."""
    horizon = _horizon_text(R, rand_stop, stop_prob, disclose_stop_prob)
    if conversation:
        interaction_rules = """
Each round has a messaging phase followed by an action phase. During the messaging
phase, you and the opponent compose messages independently. Both messages are then
revealed before either action is requested. Messages are non-binding: they may be
strategic, need not be truthful, and do not require either player to follow a
suggestion.
"""
    else:
        interaction_rules = """
There is no messaging phase. In each round, both players privately choose an action.
"""

    return f"""
=== GAME RULES ===
You are one player in {horizon}, facing another independent AI agent.
{interaction_rules}
In every round:
- The action space is Cooperate (C) or Defect (D).
- After the messaging phase, if enabled, and before choosing an action, you report
  a probability from 0 to 100 that the opponent will choose Cooperate.
- You then choose your action privately and simultaneously with the opponent.
- Both actions and both stage payoffs are revealed after action selection.
- Use only the history and memory provided to you when making decisions.

Payoff matrix:
{payoff_text(payoff)}

Reply with EXACTLY "READY" to acknowledge these rules.
"""


def tell_game_rule_no_conv(
    agent,
    payoff,
    R,
    rand_stop,
    stop_prob=None,
    disclose_stop_prob=False,
):
    """Send the no-conversation game rules to one agent.

    Args:
        agent: Agent receiving the rule prompt.
        payoff: Payoff matrix object formatted by ``payoff_text``.
        R: Number of rounds for a fixed-horizon game.
        rand_stop: Whether to use random stopping.
        stop_prob: Per-round stopping probability, if disclosed.
        disclose_stop_prob: Whether the prompt reveals the stopping probability.

    Returns:
        The agent's acknowledgement text.
    """
    prompt = _game_rule_prompt(
        payoff,
        R,
        rand_stop,
        conversation=False,
        stop_prob=stop_prob,
        disclose_stop_prob=disclose_stop_prob,
    )
    return llm_input(agent, prompt)


def tell_game_rule(
    agent,
    payoff,
    R,
    rand_stop,
    stop_prob=None,
    disclose_stop_prob=False,
):
    """Send the conversation-enabled game rules to one agent.

    Args:
        agent: Agent receiving the rule prompt.
        payoff: Payoff matrix object formatted by ``payoff_text``.
        R: Number of rounds for a fixed-horizon game.
        rand_stop: Whether to use random stopping.
        stop_prob: Per-round stopping probability, if disclosed.
        disclose_stop_prob: Whether the prompt reveals the stopping probability.

    Returns:
        The agent's acknowledgement text.
    """
    prompt = _game_rule_prompt(
        payoff,
        R,
        rand_stop,
        conversation=True,
        stop_prob=stop_prob,
        disclose_stop_prob=disclose_stop_prob,
    )
    return llm_input(agent, prompt)
