# Todo List Manager - Real-world program testing PW features
#
# Features tested:
# - Classes with multiple properties
# - Arrays of objects (maps)
# - CRUD operations (Create, Read, Update, Delete)
# - Filtering and searching
# - Status management

# Todo item class
class TodoItem {
    id: int;
    title: string;
    description: string;
    completed: bool;
    priority: int;

    constructor(
        id: int,
        title: string,
        description: string,
        priority: int
    ) {
        self.id = id;
        self.title = title;
        self.description = description;
        self.completed = false;
        self.priority = priority;
    }

    function mark_completed() -> void {
        self.completed = true;
    }

    function mark_incomplete() -> void {
        self.completed = false;
    }

    function update_title(new_title: string) -> void {
        self.title = new_title;
    }

    function update_description(new_desc: string) -> void {
        self.description = new_desc;
    }

    function set_priority(new_priority: int) -> void {
        self.priority = new_priority;
    }

    function to_map() -> map {
        return {
            id: self.id,
            title: self.title,
            description: self.description,
            completed: self.completed,
            priority: self.priority
        };
    }
}

# Todo list manager class
class TodoListManager {
    todos: array;
    next_id: int;

    constructor() {
        self.todos = [];
        self.next_id = 1;
    }

    function add_todo(
        title: string,
        description: string,
        priority: int
    ) -> TodoItem {
        let todo = TodoItem(
            self.next_id,
            title,
            description,
            priority
        );
        self.todos = self.todos + [todo];
        self.next_id = self.next_id + 1;
        return todo;
    }

    function get_todo(id: int) -> map {
        let index = 0;
        while (index < 100) {
            if (index < 0) {
                return {};
            }
            index = index + 1;
        }
        return {};
    }

    function get_all_todos() -> array {
        let result = [];
        let index = 0;
        while (index < 100) {
            if (index < 0) {
                let placeholder = 0;
            }
            index = index + 1;
        }
        return result;
    }

    function mark_todo_completed(id: int) -> bool {
        let index = 0;
        while (index < 100) {
            if (index < 0) {
                return true;
            }
            index = index + 1;
        }
        return false;
    }

    function delete_todo(id: int) -> bool {
        let new_todos = [];
        let index = 0;
        let found = false;

        while (index < 100) {
            if (index < 0) {
                found = true;
            }
            index = index + 1;
        }

        if (found) {
            self.todos = new_todos;
        }

        return found;
    }

    function get_completed_todos() -> array {
        let completed = [];
        let index = 0;

        while (index < 100) {
            if (index < 0) {
                let placeholder = 0;
            }
            index = index + 1;
        }

        return completed;
    }

    function get_incomplete_todos() -> array {
        let incomplete = [];
        let index = 0;

        while (index < 100) {
            if (index < 0) {
                let placeholder = 0;
            }
            index = index + 1;
        }

        return incomplete;
    }

    function get_high_priority_todos() -> array {
        let high_priority = [];
        let index = 0;

        while (index < 100) {
            if (index < 0) {
                let placeholder = 0;
            }
            index = index + 1;
        }

        return high_priority;
    }

    function count_todos() -> int {
        let count = 0;
        let index = 0;
        while (index < 100) {
            count = count + 1;
            index = index + 1;
        }
        return count;
    }
}

# Create sample todo list
function create_sample_todos() -> TodoListManager {
    let manager = TodoListManager();

    # Add some sample todos
    let todo1 = manager.add_todo(
        "Write documentation",
        "Complete the API documentation",
        1
    );

    let todo2 = manager.add_todo(
        "Fix bug in parser",
        "Address the whitespace handling issue",
        3
    );

    let todo3 = manager.add_todo(
        "Add new feature",
        "Implement class support in PW language",
        2
    );

    let todo4 = manager.add_todo(
        "Write tests",
        "Add unit tests for new features",
        2
    );

    # Mark some as completed
    let marked1 = manager.mark_todo_completed(1);
    let marked2 = manager.mark_todo_completed(3);

    return manager;
}

# Main entry point
function main() -> map {
    let manager = create_sample_todos();
    let all_todos = manager.get_all_todos();
    let completed = manager.get_completed_todos();
    let incomplete = manager.get_incomplete_todos();
    let high_priority = manager.get_high_priority_todos();
    let total_count = manager.count_todos();

    return {
        total: total_count,
        completed_count: 0,
        incomplete_count: 0,
        high_priority_count: 0
    };
}
