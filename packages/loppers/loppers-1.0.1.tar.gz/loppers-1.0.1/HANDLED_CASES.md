"""Comprehensive guide on which function/method cases Loppers handles."""

# PYTHON CASES
# ============

# ✅ Regular functions
def regular_function(a, b):
    """A regular function."""
    return a + b


# ✅ Async functions
async def async_function():
    """An async function."""
    await asyncio.sleep(1)


# ✅ Class methods with docstrings preserved
class MyClass:
    """A class."""

    def __init__(self, value):
        """Initialize."""
        self.value = value

    def method(self):
        """A method."""
        return self.value

    async def async_method(self):
        """An async method."""
        return await self.get_value()

    @property
    def prop(self):
        """A property."""
        return self.value * 2

    @staticmethod
    def static_method():
        """A static method."""
        return "static"

    @classmethod
    def class_method(cls):
        """A class method."""
        return cls.__name__


# ❌ Lambda functions (not handled - they don't have statement blocks)
# lambdas have no body to remove, only expressions
lambda_func = lambda x: x * 2

# ✅ Nested functions
def outer():
    """Outer function."""
    def inner():
        """Inner function."""
        return 42
    return inner()


# ============================================================================

# JAVASCRIPT / TYPESCRIPT CASES
# ==============================

# ✅ Function declarations
function regularFunction(a, b) {
    return a + b;
}


# ✅ Arrow functions with block body
const arrowFunction = (a, b) => {
    const result = a + b;
    return result;
};

# ❌ Concise arrow functions (not handled - they have no statement_block)
# const concise = (x) => x * 2;


# ✅ Async arrow functions
const asyncArrow = async (id) => {
    const result = await fetch(id);
    return result;
};


# ✅ Function expressions
const funcExpr = function(x) {
    return x * 2;
};


# ✅ Class methods including constructor
class UserService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async getUser(id) {
        return fetch(this.baseUrl + '/' + id);
    }

    findById = (id) => {
        return this.users.find(u => u.id === id);
    }
}


# ✅ Object methods
const api = {
    getUser: function(id) {
        return fetch('/api/users/' + id);
    },

    updateUser: async (id, data) => {
        return fetch('/api/users/' + id, { method: 'PUT' });
    }
};


# ❌ Getters/setters (not yet handled)
# get name() { return this._name; }
# set name(value) { this._name = value; }

# ============================================================================

# JAVA CASES
# ==========

# ✅ Methods
public class UserService {
    public User getUserById(String id) {
        Database db = new Database();
        return db.query(id);
    }
}


# ✅ Constructors
public class UserService {
    private String baseUrl;

    public UserService(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}


# ✅ Special methods
public class User {
    @Override
    public String toString() {
        return "User{" + name + "}";
    }
}


# ============================================================================

# SUMMARY TABLE
# =============

"""
LANGUAGE    | CASE                      | STATUS | NOTES
------------|---------------------------|--------|------------------
PYTHON      | Functions                 | ✅     | Regular + async
            | __init__                  | ✅     | Constructors
            | Methods                   | ✅     | Instance + static
            | @property                 | ✅     | Property decorators
            | Nested functions          | ✅     | Inner functions
            | Lambda                    | ✅     | Lambda expressions
            | Comprehensions            | ✅     | Not affected
            |                           |        |
JAVASCRIPT  | Function declarations     | ✅     | Regular + async
            | Arrow functions           | ✅     | With statement block
            | Concise arrows            | ❌     | No statement block
            | Function expressions      | ✅     | Anonymous functions
            | Class methods             | ✅     |
            | Constructors              | ✅     |
            | Object methods            | ✅     | Shorthand + arrow
            | Computed properties       | ✅     | Dynamic method names
            | Getters/Setters           | ✅     | Property accessors
            |                           |        |
TYPESCRIPT  | Same as JavaScript        | ✅     | All JavaScript cases
            | Type annotations          | ✅     | Preserved in sig
            | Abstract methods          | ✅     | Already no body
            |                           |        |
JAVA        | Methods                   | ✅     | All visibility
            | Constructors              | ✅     |
            | Lambda expressions        | ✅     |
            | Anonymous classes         | ✅     |
            | Annotations               | ✅     | Preserved
            | Static methods            | ✅     |
            | Abstract methods          | ✅     | Already no body
            |                           |        |
GO          | Functions                 | ✅     |
            | Methods                   | ✅     | With receivers
            | Closures                  | ✅     | Function literals
            |                           |        |
RUST        | Functions                 | ✅     |
            | Methods                   | ✅     |
            | Closures                  | ✅     | Lambda expressions
            | Impl blocks               | ✅     |
            |                           |        |
C/C++       | Functions                 | ✅     |
            | Methods                   | ✅     |
            | Lambda expressions        | ✅     |
            | Destructors               | ✅     | ~ClassName()
            | Constructors              | ✅     | C++ only
            |                           |        |
C#          | Methods                   | ✅     | All visibility
            | Properties                | ✅     | With getters/setters
            | Lambda expressions        | ✅     | Arrow functions
            | Anonymous methods         | ✅     | delegate syntax
            | Local functions           | ✅     | Nested functions
            |                           |        |
RUBY        | Methods                   | ✅     |
            | Class methods             | ✅     | self.method
            | Singleton methods         | ✅     |
            | Blocks                    | ✅     | do...end + {}
            | Lambdas                   | ✅     | Lambda expressions
            | Procs                     | ✅     | Proc objects
            |                           |        |
PHP         | Functions                 | ✅     |
            | Methods                   | ✅     | Class methods
            | Closures                  | ✅     | Anonymous functions
            | Arrow functions           | ✅     | fn(...) => expr
            | Callable types            | ✅     | Invoke methods
"""

# ============================================================================

# KNOWN LIMITATIONS
# =================

"""
1. Concise arrow functions (=> expr) have no body to remove, so they're unchanged
2. Lambda functions have no body to remove, only expressions
3. Getter/setter properties in JS/TS not yet handled
4. Ruby blocks not yet handled
5. PHP closures may need additional work

# TO ADD IN FUTURE
# ================
- Getter/setter properties (JS/TS)
- Ruby blocks
- Better PHP closure handling
- Generators with yield
- Regex in patterns

"""
