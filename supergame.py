"""Run one repeated Prisoner's Dilemma supergame between two LLM agents."""

import random
import re
from typing import Optional

from agent import llm_input


def get_payoff(action0: int, action1: int, payoff):
    """Return the two players' stage-game payoffs for encoded actions.

    Args:
        action0: Player 0's action, encoded as 0 for cooperation or 1 for
            defection.
        action1: Player 1's action using the same encoding.
        payoff: A payoff object exposing ``get_payoff(action0, action1)``.

    Returns:
        A ``(payoff_0, payoff_1)`` tuple.
    """
    return payoff.get_payoff(action0, action1)


def cd_decode(num: int) -> str:
    """Convert an encoded action to ``"C"`` or ``"D"``.

    Raises:
        ValueError: If ``num`` is not a valid encoded action.
    """
    if num == 0:
        return "C"
    if num == 1:
        return "D"
    raise ValueError(f"Invalid encoded action: {num!r}")


def action_encode(text: str) -> int:
    """Parse an LLM action response and encode cooperation as 0, defection as 1.

    The action prompt requests exactly one word, but the parser tolerates a short
    sentence when it contains one unambiguous action. Invalid or ambiguous output
    raises an error instead of silently defaulting to cooperation and biasing the
    experimental data.

    Raises:
        TypeError: If ``text`` is not a string.
        ValueError: If no unique action can be recovered from the response.
    """
    if not isinstance(text, str):
        raise TypeError("Action response must be a string.")

    normalized = text.strip().lower()
    if normalized in {"c", "cooperate"}:
        return 0
    if normalized in {"d", "defect"}:
        return 1

    tokens = re.findall(r"\b(?:cooperate|defect)\b", normalized)
    actions = {0 if token == "cooperate" else 1 for token in tokens}
    if len(actions) == 1:
        return actions.pop()
    raise ValueError(f"Could not parse a unique action from response: {text!r}")


def belief_encode(text: str) -> float:
    """Parse one 0--100 belief report and return it on the 0--1 scale.

    A response such as ``"75"`` or ``"75%"`` is stored as ``0.75``. The
    function rejects responses containing no valid probability or more than one
    number, since either case would make the recorded belief ambiguous.

    Raises:
        TypeError: If ``text`` is not a string.
        ValueError: If the response does not contain exactly one value in
            ``[0, 100]``.
    """
    if not isinstance(text, str):
        raise TypeError("Belief response must be a string.")

    numbers = re.findall(r"(?<![\d.])(?:100(?:\.0+)?|\d{1,2}(?:\.\d+)?)(?![\d.])", text)
    if len(numbers) != 1:
        raise ValueError(f"Expected one belief value from 0 to 100, got: {text!r}")

    value = float(numbers[0])
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"Belief value is outside [0, 100]: {value}")
    return value / 100.0


def _round_info(r: int, total_rounds: int, rand_stop: bool, phase: str) -> str:
    """Build the round-and-phase label used in agent prompts."""
    if rand_stop:
        return f"Round {r} -- {phase}. The game may end randomly after this round."
    return f"Round {r} out of {total_rounds} -- {phase}."


def message_request(agent, r: int, R: int, rand_stop: bool) -> str:
    """Ask an agent to compose its simultaneous pre-action message.

    Args:
        agent: The agent that will send the message.
        r: Current round number, starting at 1.
        R: Total rounds in a fixed-horizon game. Ignored for random stopping.
        rand_stop: Whether the supergame has a random horizon.

    Returns:
        The agent's message with surrounding whitespace removed by ``llm_input``.
    """
    prompt = f"""
{_round_info(r, R, rand_stop, "Messaging Phase")}
Compose a message to the opponent in at most 50 words. Do not state that you have
already selected an action; actions will be chosen only after both messages are
revealed.
"""
    return llm_input(agent, prompt)


def belief_elicitation(
    agent,
    r: int,
    R: int,
    rand_stop: bool,
    own_message: Optional[str] = None,
    opponent_message: Optional[str] = None,
) -> float:
    """Elicit the agent's belief after messaging and before action selection.

    In a conversation treatment, both simultaneously composed messages are
    included in the elicitation prompt. The LLM reports an integer probability
    from 0 to 100, which is normalized to ``[0, 1]`` for calibration and
    Brier-score analysis.
    """
    message_context = ""
    if own_message is not None or opponent_message is not None:
        if own_message is None or opponent_message is None:
            raise ValueError("Both messages must be supplied together.")
        message_context = f"""
Both simultaneous messages have now been revealed.

Your message:
<your_message>{own_message}</your_message>

Opponent's message:
<opponent_message>{opponent_message}</opponent_message>
"""

    prompt = f"""
{_round_info(r, R, rand_stop, "Belief Report")}
{message_context}
No action has been selected yet. Based on the information currently available,
what probability do you assign to the opponent choosing Cooperate in this round?
Respond with EXACTLY ONE INTEGER from 0 to 100 and nothing else.
"""
    return belief_encode(llm_input(agent, prompt))


def action_request(
    agent,
    r: int,
    R: int,
    rand_stop: bool,
    own_message: str,
    opponent_message: str,
) -> str:
    """Request an action after revealing both simultaneous messages.

    The opponent's action remains private. Only the two messages are included in
    this prompt.
    """
    prompt = f"""
{_round_info(r, R, rand_stop, "Action Phase")}
Both messages have now been revealed.

Your message:
<your_message>{own_message}</your_message>

Opponent's message:
<opponent_message>{opponent_message}</opponent_message>

Choose your action. Respond with EXACTLY ONE WORD: "Cooperate" or "Defect" and
nothing else.
"""
    return llm_input(agent, prompt)


def action_request_no_conv(agent, r: int, R: int, rand_stop: bool) -> str:
    """Request an action in a round without a messaging phase."""
    prompt = f"""
{_round_info(r, R, rand_stop, "Action Phase")}
Choose your action. Respond with EXACTLY ONE WORD: "Cooperate" or "Defect" and
nothing else.
"""
    return llm_input(agent, prompt)


def outcome_feedback(
    agent,
    r: int,
    own_action: int,
    opponent_action: int,
    own_payoff,
    opponent_payoff,
    own_cumulative_payoff,
    opponent_cumulative_payoff,
) -> str:
    """Reveal the completed round outcome so it enters the agent's memory."""
    prompt = f"""
Round {r} is complete.
Your action: {cd_decode(own_action)}
Opponent's action: {cd_decode(opponent_action)}
Your payoff this round: {own_payoff}
Opponent's payoff this round: {opponent_payoff}
Your cumulative payoff: {own_cumulative_payoff}
Opponent's cumulative payoff: {opponent_cumulative_payoff}
Reply with EXACTLY "OK" to acknowledge this feedback.
"""
    return llm_input(agent, prompt)


def match(
    P0,
    P1,
    conversation,
    payoff,
    R,
    rand_stop=False,
    stop_prob=0.1,
    rng=None,
):
    """Run one complete repeated-game match and return round-level records.

    Args:
        P0: Player 0 agent.
        P1: Player 1 agent.
        conversation: If true, collect simultaneous messages before each action.
        payoff: Stage-game payoff object.
        R: Number of rounds for a fixed-horizon game.
        rand_stop: If true, use independent geometric stopping after each round.
        stop_prob: Per-round stopping probability for a random-horizon game.
        rng: Optional random-number generator exposing ``random()``. If omitted,
            the module-level ``random`` generator is used.

    Returns:
        A list of dictionaries, one per completed round, containing messages,
        normalized beliefs, actions, stage payoffs, and cumulative payoffs.

    Raises:
        ValueError: If the horizon parameters are invalid.
    """
    if not rand_stop and (not isinstance(R, int) or R < 1):
        raise ValueError("R must be a positive integer for a fixed-horizon match.")
    if rand_stop and not 0.0 < stop_prob <= 1.0:
        raise ValueError("stop_prob must lie in (0, 1].")

    history = []
    cumulative_payoff_0 = 0
    cumulative_payoff_1 = 0
    max_rounds = 1_000_000 if rand_stop else R
    stopping_rng = rng if rng is not None else random

    for r in range(1, max_rounds + 1):
        if conversation:
            # Messages are composed independently, then both are revealed.
            message_0 = message_request(P0, r, R, rand_stop)
            message_1 = message_request(P1, r, R, rand_stop)

            # Beliefs are measured after both messages are available and before
            # either action is selected, matching the planned causal chain:
            # message content -> belief -> action.
            belief_0 = belief_elicitation(
                P0, r, R, rand_stop, message_0, message_1
            )
            belief_1 = belief_elicitation(
                P1, r, R, rand_stop, message_1, message_0
            )

            action_0 = action_encode(
                action_request(P0, r, R, rand_stop, message_0, message_1)
            )
            action_1 = action_encode(
                action_request(P1, r, R, rand_stop, message_1, message_0)
            )
        else:
            message_0, message_1 = None, None
            belief_0 = belief_elicitation(P0, r, R, rand_stop)
            belief_1 = belief_elicitation(P1, r, R, rand_stop)
            action_0 = action_encode(action_request_no_conv(P0, r, R, rand_stop))
            action_1 = action_encode(action_request_no_conv(P1, r, R, rand_stop))

        payoff_0, payoff_1 = get_payoff(action_0, action_1, payoff)
        cumulative_payoff_0 += payoff_0
        cumulative_payoff_1 += payoff_1

        history.append(
            {
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
            }
        )

        # Explicit feedback is required; otherwise the agents' response-chain
        # memory would never contain the opponent's action or realized payoffs.
        outcome_feedback(
            P0,
            r,
            action_0,
            action_1,
            payoff_0,
            payoff_1,
            cumulative_payoff_0,
            cumulative_payoff_1,
        )
        outcome_feedback(
            P1,
            r,
            action_1,
            action_0,
            payoff_1,
            payoff_0,
            cumulative_payoff_1,
            cumulative_payoff_0,
        )

        if rand_stop and stopping_rng.random() < stop_prob:
            break

    return history
