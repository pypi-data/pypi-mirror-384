
function is_valid_state(state: string) -> bool {
    @requires non_empty_state: len(state) > 0

    @ensures validation_complete: result == true || result == false

    if (state == "idle") {
        return true;
    }

    if (state == "active") {
        return true;
    }

    if (state == "paused") {
        return true;
    }

    if (state == "completed") {
        return true;
    }

    if (state == "failed") {
        return true;
    }

    if (state == "cancelled") {
        return true;
    }

    return false;
}

function can_transition(
    from_state: string,
    to_state: string
) -> bool {
    @requires valid_from: len(from_state) > 0
    @requires valid_to: len(to_state) > 0

    @ensures transition_decided: result == true || result == false

    if (from_state == "idle") {
        if (to_state == "active" || to_state == "cancelled") {
            return true;
        }
        return false;
    }

    if (from_state == "active") {
        if (to_state == "paused" || to_state == "completed" || to_state == "failed" || to_state == "cancelled") {
            return true;
        }
        return false;
    }

    if (from_state == "paused") {
        if (to_state == "active" || to_state == "cancelled") {
            return true;
        }
        return false;
    }

    if (from_state == "completed") {
        return false;
    }

    if (from_state == "failed") {
        if (to_state == "idle") {
            return true;
        }
        return false;
    }

    if (from_state == "cancelled") {
        return false;
    }

    return false;
}

function validate_state_data(
    state: string,
    data_present: bool,
    data_valid: bool
) -> bool {
    @requires valid_state: len(state) > 0

    @ensures data_validated: result == true || result == false

    if (state == "idle") {
        return true;
    }

    if (state == "active") {
        if (data_present == false) {
            return false;
        }
        if (data_valid == false) {
            return false;
        }
        return true;
    }

    if (state == "paused") {
        if (data_present == false) {
            return false;
        }
        return true;
    }

    if (state == "completed") {
        if (data_present == false) {
            return false;
        }
        if (data_valid == false) {
            return false;
        }
        return true;
    }

    if (state == "failed") {
        return true;
    }

    if (state == "cancelled") {
        return true;
    }

    return false;
}

function check_entry_condition(
    target_state: string,
    precondition_met: bool
) -> bool {
    @requires valid_target: len(target_state) > 0

    @ensures entry_checked: result == true || result == false

    if (target_state == "idle") {
        return true;
    }

    if (target_state == "active") {
        if (precondition_met == false) {
            return false;
        }
        return true;
    }

    if (target_state == "paused") {
        return true;
    }

    if (target_state == "completed") {
        if (precondition_met == false) {
            return false;
        }
        return true;
    }

    if (target_state == "failed") {
        return true;
    }

    if (target_state == "cancelled") {
        return true;
    }

    return false;
}

function check_exit_condition(
    source_state: string,
    cleanup_done: bool
) -> bool {
    @requires valid_source: len(source_state) > 0

    @ensures exit_checked: result == true || result == false

    if (source_state == "idle") {
        return true;
    }

    if (source_state == "active") {
        if (cleanup_done == false) {
            return false;
        }
        return true;
    }

    if (source_state == "paused") {
        return true;
    }

    if (source_state == "completed") {
        return false;
    }

    if (source_state == "failed") {
        return true;
    }

    if (source_state == "cancelled") {
        return false;
    }

    return false;
}

function is_terminal_state(state: string) -> bool {
    @requires valid_state: len(state) > 0

    @ensures terminal_checked: result == true || result == false

    if (state == "completed" || state == "cancelled") {
        return true;
    }

    return false;
}

function can_retry_from_state(state: string) -> bool {
    @requires valid_state: len(state) > 0

    @ensures retry_decided: result == true || result == false

    if (state == "failed") {
        return true;
    }

    return false;
}

function validate_transition_guard(
    from_state: string,
    to_state: string,
    guard_condition: bool
) -> bool {
    @requires valid_from: len(from_state) > 0
    @requires valid_to: len(to_state) > 0

    @ensures guard_validated: result == true || result == false

    if (guard_condition == false) {
        return false;
    }

    if (from_state == "active" && to_state == "completed") {
        return true;
    }

    if (from_state == "paused" && to_state == "active") {
        return true;
    }

    return true;
}

function count_transitions(
    transition_count: int,
    max_transitions: int
) -> bool {
    @requires valid_count: transition_count >= 0
    @requires positive_max: max_transitions > 0

    @ensures count_validated: result == true || result == false

    if (transition_count >= max_transitions) {
        return false;
    }

    return true;
}

function validate_state_duration(
    time_in_state: int,
    min_duration: int,
    max_duration: int
) -> bool {
    @requires valid_time: time_in_state >= 0
    @requires valid_min: min_duration >= 0
    @requires valid_max: max_duration >= min_duration

    @ensures duration_validated: result == true || result == false

    if (time_in_state < min_duration) {
        return false;
    }

    if (time_in_state > max_duration) {
        return false;
    }

    return true;
}

function check_state_timeout(
    time_in_state: int,
    timeout_seconds: int
) -> bool {
    @requires valid_time: time_in_state >= 0
    @requires positive_timeout: timeout_seconds > 0

    @ensures timeout_checked: result == true || result == false

    if (time_in_state >= timeout_seconds) {
        return true;
    }

    return false;
}

function validate_parallel_states(
    state_a: string,
    state_b: string
) -> bool {
    @requires valid_a: len(state_a) > 0
    @requires valid_b: len(state_b) > 0

    @ensures parallel_validated: result == true || result == false

    if (state_a == state_b) {
        return false;
    }

    if (state_a == "completed" && state_b == "active") {
        return false;
    }

    if (state_a == "active" && state_b == "completed") {
        return false;
    }

    return true;
}

function check_composite_state(
    parent_state: string,
    child_state: string
) -> bool {
    @requires valid_parent: len(parent_state) > 0
    @requires valid_child: len(child_state) > 0

    @ensures composite_validated: result == true || result == false

    if (parent_state == "active") {
        if (child_state == "processing" || child_state == "waiting" || child_state == "executing") {
            return true;
        }
        return false;
    }

    if (parent_state == "paused") {
        if (child_state == "suspended" || child_state == "interrupted") {
            return true;
        }
        return false;
    }

    return false;
}

function validate_state_history(
    previous_state: string,
    current_state: string,
    can_return: bool
) -> bool {
    @requires valid_previous: len(previous_state) > 0
    @requires valid_current: len(current_state) > 0

    @ensures history_validated: result == true || result == false

    if (can_return == false) {
        return true;
    }

    if (previous_state == "active" && current_state == "paused") {
        return true;
    }

    if (previous_state == "paused" && current_state == "active") {
        return true;
    }

    return false;
}

function check_concurrent_transition(
    active_transitions: int,
    max_concurrent: int
) -> bool {
    @requires valid_active: active_transitions >= 0
    @requires positive_max: max_concurrent > 0

    @ensures concurrent_validated: result == true || result == false

    if (active_transitions >= max_concurrent) {
        return false;
    }

    return true;
}

function validate_state_invariant(
    state: string,
    resource_allocated: bool,
    resource_count: int
) -> bool {
    @requires valid_state: len(state) > 0
    @requires valid_count: resource_count >= 0

    @ensures invariant_validated: result == true || result == false

    if (state == "idle") {
        if (resource_allocated == true) {
            return false;
        }
        if (resource_count > 0) {
            return false;
        }
        return true;
    }

    if (state == "active") {
        if (resource_allocated == false) {
            return false;
        }
        if (resource_count == 0) {
            return false;
        }
        return true;
    }

    if (state == "paused") {
        if (resource_allocated == false) {
            return false;
        }
        return true;
    }

    if (state == "completed") {
        if (resource_allocated == true) {
            return false;
        }
        return true;
    }

    return true;
}

function check_rollback_allowed(
    current_state: string,
    previous_state: string
) -> bool {
    @requires valid_current: len(current_state) > 0
    @requires valid_previous: len(previous_state) > 0

    @ensures rollback_decided: result == true || result == false

    if (current_state == "failed") {
        if (previous_state == "active" || previous_state == "paused") {
            return true;
        }
        return false;
    }

    return false;
}

function validate_batch_transition(
    states_count: int,
    transitions_count: int
) -> bool {
    @requires valid_states: states_count > 0
    @requires valid_transitions: transitions_count >= 0

    @ensures batch_validated: result == true || result == false

    if (transitions_count > states_count) {
        return false;
    }

    return true;
}

function check_state_dependencies(
    state: string,
    dependency_satisfied: bool
) -> bool {
    @requires valid_state: len(state) > 0

    @ensures dependencies_checked: result == true || result == false

    if (state == "active") {
        if (dependency_satisfied == false) {
            return false;
        }
        return true;
    }

    return true;
}

function validate_state_transition_path(
    start_state: string,
    end_state: string,
    intermediate_states: int
) -> bool {
    @requires valid_start: len(start_state) > 0
    @requires valid_end: len(end_state) > 0
    @requires valid_intermediate: intermediate_states >= 0

    @ensures path_validated: result == true || result == false

    if (start_state == end_state) {
        if (intermediate_states > 0) {
            return false;
        }
        return true;
    }

    if (start_state == "idle" && end_state == "completed") {
        if (intermediate_states < 1) {
            return false;
        }
        return true;
    }

    return true;
}
