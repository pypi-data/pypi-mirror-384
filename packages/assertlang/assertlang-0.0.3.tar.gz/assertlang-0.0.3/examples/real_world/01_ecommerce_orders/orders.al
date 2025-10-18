// E-commerce Order System with Contract Validation
// Demonstrates validation contracts, business rules, and state management

// Validate order creation inputs
function validate_order_inputs(
    order_id: string,
    customer_id: string,
    total_amount: float,
    item_count: int
) -> bool {
    @requires valid_order_id: len(order_id) > 0
    @requires valid_customer_id: len(customer_id) > 0
    @requires positive_amount: total_amount > 0.0
    @requires has_items: item_count > 0

    @ensures validation_result: result == true || result == false

    // All checks passed
    return true;
}

// Validate payment information
function validate_payment(
    payment_method: string,
    transaction_id: string,
    amount: float
) -> bool {
    @requires valid_payment_method: len(payment_method) > 0
    @requires valid_transaction: len(transaction_id) > 0
    @requires positive_payment: amount > 0.0

    @ensures validation_complete: result == true || result == false

    // Payment validation passed
    return true;
}

// Validate shipping information
function validate_shipping(
    tracking_number: string,
    carrier: string,
    address: string
) -> bool {
    @requires valid_tracking: len(tracking_number) > 0
    @requires valid_carrier: len(carrier) > 0
    @requires valid_address: len(address) > 0

    @ensures validation_complete: result == true || result == false

    return true;
}

// Check if order can be cancelled
function can_cancel_order(
    status: string,
    is_shipped: bool
) -> bool {
    @requires valid_status: len(status) > 0

    @ensures cancellation_possible: result == true || result == false

    // Can only cancel if not shipped
    if (is_shipped == true) {
        return false;
    }

    return true;
}

// Validate refund amount
function validate_refund(
    refund_amount: float,
    original_amount: float
) -> bool {
    @requires positive_refund: refund_amount > 0.0
    @requires positive_original: original_amount > 0.0
    @requires refund_not_exceeds: refund_amount <= original_amount

    @ensures refund_valid: result == true

    return true;
}

// Calculate order total with tax
function calculate_total_with_tax(
    subtotal: float,
    tax_rate: float
) -> float {
    @requires positive_subtotal: subtotal >= 0.0
    @requires valid_tax_rate: tax_rate >= 0.0 && tax_rate <= 1.0

    @ensures total_includes_tax: result >= subtotal

    let tax_amount = subtotal * tax_rate;
    let total = subtotal + tax_amount;

    return total;
}

// Apply discount to order
function apply_discount(
    original_price: float,
    discount_percent: float
) -> float {
    @requires positive_price: original_price > 0.0
    @requires valid_discount: discount_percent >= 0.0 && discount_percent <= 100.0

    @ensures discounted_price: result >= 0.0 && result <= original_price

    let discount_amount = original_price * (discount_percent / 100.0);
    let final_price = original_price - discount_amount;

    return final_price;
}

// Validate order status transition
function can_transition_status(
    current_status: string,
    new_status: string
) -> bool {
    @requires valid_current: len(current_status) > 0
    @requires valid_new: len(new_status) > 0

    @ensures transition_decided: result == true || result == false

    // Simplified state machine validation
    // pending -> payment_confirmed -> processing -> shipped -> delivered

    if (current_status == "pending") {
        if (new_status == "payment_confirmed" || new_status == "cancelled") {
            return true;
        }
    }

    if (current_status == "payment_confirmed") {
        if (new_status == "processing" || new_status == "cancelled") {
            return true;
        }
    }

    if (current_status == "processing") {
        if (new_status == "shipped" || new_status == "cancelled") {
            return true;
        }
    }

    if (current_status == "shipped") {
        if (new_status == "delivered") {
            return true;
        }
    }

    if (current_status == "delivered") {
        if (new_status == "refunded") {
            return true;
        }
    }

    return false;
}

// Check if order is in final state
function is_final_state(status: string) -> bool {
    @requires valid_status: len(status) > 0

    @ensures is_boolean: result == true || result == false

    if (status == "delivered" || status == "cancelled" || status == "refunded") {
        return true;
    }

    return false;
}

// Validate order items count
function validate_item_count(item_count: int, max_items_per_order: int) -> bool {
    @requires positive_count: item_count > 0
    @requires positive_max: max_items_per_order > 0

    @ensures count_valid: result == true || result == false

    if (item_count > max_items_per_order) {
        return false;
    }

    return true;
}
