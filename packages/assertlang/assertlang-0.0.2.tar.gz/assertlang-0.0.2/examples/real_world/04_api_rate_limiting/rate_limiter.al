// API Rate Limiting with Contract-Based Validation
// Demonstrates time-based contracts and token bucket algorithm

// Validate rate limit configuration
function validate_rate_limit_config(
    requests_per_window: int,
    window_seconds: int,
    burst_size: int
) -> bool {
    @requires positive_requests: requests_per_window > 0
    @requires positive_window: window_seconds > 0 && window_seconds <= 86400
    @requires valid_burst: burst_size >= requests_per_window

    @ensures config_valid: result == true

    return true;
}

// Check if request allowed under rate limit
function is_request_allowed(
    current_token_count: int,
    tokens_required: int,
    max_tokens: int
) -> bool {
    @requires valid_current: current_token_count >= 0
    @requires valid_required: tokens_required > 0
    @requires valid_max: max_tokens > 0

    @ensures decision_made: result == true || result == false

    // Must have enough tokens
    if (current_token_count < tokens_required) {
        return false;
    }

    // Cannot exceed max tokens
    if (current_token_count > max_tokens) {
        return false;
    }

    return true;
}

// Calculate tokens to add based on time elapsed
function calculate_tokens_to_add(
    elapsed_seconds: int,
    refill_rate: int,
    current_tokens: int,
    max_tokens: int
) -> int {
    @requires valid_elapsed: elapsed_seconds >= 0
    @requires positive_refill: refill_rate > 0
    @requires valid_current: current_tokens >= 0 && current_tokens <= max_tokens
    @requires positive_max: max_tokens > 0

    @ensures valid_result: result >= 0

    // Calculate new tokens based on elapsed time
    let tokens_to_add = elapsed_seconds * refill_rate;

    // Would new tokens exceed max?
    let potential_total = current_tokens + tokens_to_add;

    if (potential_total > max_tokens) {
        // Cap at max tokens
        tokens_to_add = max_tokens - current_tokens;
    }

    return tokens_to_add;
}

// Validate quota limits
function validate_quota_limit(
    used_quota: int,
    total_quota: int,
    warning_threshold: int
) -> bool {
    @requires valid_used: used_quota >= 0
    @requires positive_total: total_quota > 0
    @requires valid_threshold: warning_threshold > 0 && warning_threshold <= total_quota

    @ensures quota_validated: result == true || result == false

    // Cannot exceed total quota
    if (used_quota > total_quota) {
        return false;
    }

    return true;
}

// Check if quota warning threshold reached
function is_quota_warning_threshold_reached(
    used_quota: int,
    total_quota: int,
    warning_percentage: int
) -> bool {
    @requires valid_used: used_quota >= 0
    @requires positive_total: total_quota > 0
    @requires valid_percentage: warning_percentage > 0 && warning_percentage <= 100

    @ensures threshold_checked: result == true || result == false

    // Calculate threshold: used * 100 > total * warning_percentage
    if (used_quota * 100 >= total_quota * warning_percentage) {
        return true;
    }

    return false;
}

// Validate tier limits
function validate_tier_limits(
    tier: string,
    requests_per_minute: int,
    daily_quota: int
) -> bool {
    @requires valid_tier: len(tier) > 0
    @requires positive_requests: requests_per_minute > 0
    @requires positive_quota: daily_quota > 0

    @ensures tier_validated: result == true || result == false

    // Free tier: max 10 req/min, 1000/day
    if (tier == "free") {
        if (requests_per_minute > 10) {
            return false;
        }
        if (daily_quota > 1000) {
            return false;
        }
        return true;
    }

    // Basic tier: max 100 req/min, 50000/day
    if (tier == "basic") {
        if (requests_per_minute > 100) {
            return false;
        }
        if (daily_quota > 50000) {
            return false;
        }
        return true;
    }

    // Pro tier: max 1000 req/min, 1000000/day
    if (tier == "pro") {
        if (requests_per_minute > 1000) {
            return false;
        }
        if (daily_quota > 1000000) {
            return false;
        }
        return true;
    }

    // Enterprise tier: max 10000 req/min, 10000000/day
    if (tier == "enterprise") {
        if (requests_per_minute > 10000) {
            return false;
        }
        if (daily_quota > 10000000) {
            return false;
        }
        return true;
    }

    // Unknown tier
    return false;
}

// Calculate retry after seconds
function calculate_retry_after_seconds(
    tokens_needed: int,
    current_tokens: int,
    refill_rate: int
) -> int {
    @requires positive_needed: tokens_needed > 0
    @requires valid_current: current_tokens >= 0
    @requires positive_refill: refill_rate > 0

    @ensures valid_retry: result >= 0

    // Calculate how many tokens short
    let tokens_short = tokens_needed - current_tokens;

    if (tokens_short <= 0) {
        // Already have enough tokens
        return 0;
    }

    // Calculate seconds needed to refill
    let seconds_needed = tokens_short / refill_rate;

    // Account for remainder
    if (tokens_short % refill_rate > 0) {
        seconds_needed = seconds_needed + 1;
    }

    return seconds_needed;
}

// Validate burst allowance
function is_burst_allowed(
    burst_size: int,
    normal_rate: int,
    requests_in_burst: int
) -> bool {
    @requires positive_burst: burst_size > 0
    @requires positive_rate: normal_rate > 0
    @requires valid_requests: requests_in_burst >= 0

    @ensures burst_decided: result == true || result == false

    // Burst size must be larger than normal rate
    if (burst_size <= normal_rate) {
        return false;
    }

    // Requests in burst cannot exceed burst size
    if (requests_in_burst > burst_size) {
        return false;
    }

    return true;
}

// Validate time window
function is_valid_time_window(
    window_start: int,
    window_end: int,
    current_time: int
) -> bool {
    @requires valid_start: window_start >= 0
    @requires valid_end: window_end >= 0
    @requires valid_current: current_time >= 0

    @ensures window_validated: result == true || result == false

    // Window end must be after start
    if (window_end <= window_start) {
        return false;
    }

    // Current time should be after or at window start
    if (current_time < window_start) {
        return false;
    }

    return true;
}

// Check if rate limit reset needed
function should_reset_rate_limit(
    last_reset_time: int,
    current_time: int,
    reset_interval: int
) -> bool {
    @requires valid_last_reset: last_reset_time >= 0
    @requires valid_current: current_time >= 0
    @requires positive_interval: reset_interval > 0

    @ensures reset_decided: result == true || result == false

    let time_since_reset = current_time - last_reset_time;

    if (time_since_reset >= reset_interval) {
        return true;
    }

    return false;
}

// Validate concurrent request limit
function validate_concurrent_requests(
    active_requests: int,
    max_concurrent: int
) -> bool {
    @requires valid_active: active_requests >= 0
    @requires positive_max: max_concurrent > 0

    @ensures concurrent_validated: result == true || result == false

    if (active_requests >= max_concurrent) {
        return false;
    }

    return true;
}

// Calculate cost for request (weighted rate limiting)
function calculate_request_cost(
    endpoint_type: string,
    payload_size_kb: int
) -> int {
    @requires valid_endpoint: len(endpoint_type) > 0
    @requires valid_size: payload_size_kb >= 0

    @ensures positive_cost: result > 0

    let base_cost = 1;

    // Read operations: 1 token
    if (endpoint_type == "read") {
        base_cost = 1;
    }

    // Write operations: 5 tokens
    if (endpoint_type == "write") {
        base_cost = 5;
    }

    // Delete operations: 10 tokens
    if (endpoint_type == "delete") {
        base_cost = 10;
    }

    // Search operations: 3 tokens
    if (endpoint_type == "search") {
        base_cost = 3;
    }

    // Add cost for large payloads (1 token per 100KB)
    let size_cost = payload_size_kb / 100;
    if (payload_size_kb % 100 > 0) {
        size_cost = size_cost + 1;
    }

    let total_cost = base_cost + size_cost;

    return total_cost;
}

// Validate IP-based rate limit
function validate_ip_rate_limit(
    requests_from_ip: int,
    max_requests_per_ip: int,
    time_window_seconds: int
) -> bool {
    @requires valid_requests: requests_from_ip >= 0
    @requires positive_max: max_requests_per_ip > 0
    @requires positive_window: time_window_seconds > 0

    @ensures ip_limit_validated: result == true || result == false

    if (requests_from_ip > max_requests_per_ip) {
        return false;
    }

    return true;
}

// Check if cooldown period active
function is_cooldown_active(
    last_violation_time: int,
    current_time: int,
    cooldown_seconds: int
) -> bool {
    @requires valid_last_violation: last_violation_time >= 0
    @requires valid_current: current_time >= 0
    @requires positive_cooldown: cooldown_seconds > 0

    @ensures cooldown_checked: result == true || result == false

    let time_since_violation = current_time - last_violation_time;

    if (time_since_violation < cooldown_seconds) {
        return true;  // Still in cooldown
    }

    return false;  // Cooldown expired
}

// Validate global rate limit
function validate_global_rate_limit(
    total_requests: int,
    max_global_requests: int,
    time_window_seconds: int
) -> bool {
    @requires valid_total: total_requests >= 0
    @requires positive_max: max_global_requests > 0
    @requires positive_window: time_window_seconds > 0

    @ensures global_limit_validated: result == true || result == false

    if (total_requests > max_global_requests) {
        return false;
    }

    return true;
}

// Calculate penalty for rate limit violation
function calculate_violation_penalty(
    violation_count: int,
    base_penalty_seconds: int
) -> int {
    @requires valid_count: violation_count >= 0
    @requires positive_base: base_penalty_seconds > 0

    @ensures positive_penalty: result > 0

    // Exponential backoff: penalty = base * 2^violations (capped at 10 violations)
    // Use lookup approach to avoid complex loops

    let multiplier = 1;

    // 2^0 = 1
    if (violation_count == 0) {
        multiplier = 1;
    }

    // 2^1 = 2
    if (violation_count == 1) {
        multiplier = 2;
    }

    // 2^2 = 4
    if (violation_count == 2) {
        multiplier = 4;
    }

    // 2^3 = 8
    if (violation_count == 3) {
        multiplier = 8;
    }

    // 2^4 = 16
    if (violation_count == 4) {
        multiplier = 16;
    }

    // 2^5 = 32
    if (violation_count == 5) {
        multiplier = 32;
    }

    // 2^6 = 64
    if (violation_count == 6) {
        multiplier = 64;
    }

    // 2^7 = 128
    if (violation_count == 7) {
        multiplier = 128;
    }

    // 2^8 = 256
    if (violation_count == 8) {
        multiplier = 256;
    }

    // 2^9 = 512
    if (violation_count == 9) {
        multiplier = 512;
    }

    // 2^10+ = 1024 (cap at 10 violations)
    if (violation_count >= 10) {
        multiplier = 1024;
    }

    let penalty = base_penalty_seconds * multiplier;

    return penalty;
}
