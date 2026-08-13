from typing import Dict, Any
from examiner.enums import Part, ExaminerState
from examiner.actions import ExaminerAction


# Transition matrix mapping (current_state -> { action_name -> next_state })
TRANSITIONS: Dict[str, Dict[str, str]] = {
    "introduction": {
        ExaminerAction.ASK_NEXT.value: ExaminerState.PART1.value,
        ExaminerAction.MOVE_PART.value: ExaminerState.PART1.value
    },
    "part1": {
        ExaminerAction.ASK_NEXT.value: ExaminerState.PART1.value,
        ExaminerAction.REPEAT.value: ExaminerState.PART1.value,
        ExaminerAction.CLARIFY.value: ExaminerState.PART1.value,
        ExaminerAction.MOVE_PART.value: ExaminerState.PART2_INTRO.value
    },
    "part2_intro": {
        ExaminerAction.ASK_NEXT.value: ExaminerState.PART2_PREPARATION.value,
        ExaminerAction.MOVE_PART.value: ExaminerState.PART2_PREPARATION.value
    },
    "part2_preparation": {
        ExaminerAction.ASK_NEXT.value: ExaminerState.PART2_SPEAKING.value,
        ExaminerAction.START_SPEAKING.value: ExaminerState.PART2_SPEAKING.value,
        ExaminerAction.MOVE_PART.value: ExaminerState.PART2_SPEAKING.value
    },
    "part2_speaking": {
        ExaminerAction.ASK_NEXT.value: ExaminerState.PART2_SPEAKING.value,
        ExaminerAction.END_PART.value: ExaminerState.PART3.value,
        ExaminerAction.MOVE_PART.value: ExaminerState.PART3.value
    },
    "part3": {
        ExaminerAction.ASK_NEXT.value: ExaminerState.PART3.value,
        ExaminerAction.REPEAT.value: ExaminerState.PART3.value,
        ExaminerAction.CLARIFY.value: ExaminerState.PART3.value,
        ExaminerAction.END_TEST.value: ExaminerState.ENDING.value,
        ExaminerAction.MOVE_PART.value: ExaminerState.ENDING.value
    },
    "ending": {
        ExaminerAction.END_TEST.value: ExaminerState.COMPLETED.value
    },
    "completed": {}
}


def is_valid_transition(current_state: str, action: str) -> bool:
    """
    Checks whether an action is legal for the current examiner state in the transition matrix.
    """
    act_val = action.value if isinstance(action, ExaminerAction) else str(action)
    state_transitions = TRANSITIONS.get(current_state, {})
    return act_val in state_transitions


def validate_transition(current_state: str, action: str) -> str:
    """
    Level 3 Validation: Validates that action is legal from current_state.
    Raises ValueError if transition is forbidden from current_state.
    Returns target state if valid.
    """
    act_val = action.value if isinstance(action, ExaminerAction) else str(action)
    state_transitions = TRANSITIONS.get(current_state, {})
    if act_val not in state_transitions:
        raise ValueError(f"Action '{act_val}' is not allowed from state '{current_state}'.")
    return state_transitions[act_val]


def get_next_state(current_state: str, action: str) -> str:
    """
    Returns the target state after executing action in current_state.
    Returns current_state if transition is unknown or forbidden.
    """
    try:
        return validate_transition(current_state, action)
    except ValueError:
        return current_state
