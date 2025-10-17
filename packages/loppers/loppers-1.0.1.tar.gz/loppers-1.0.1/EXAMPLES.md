# Before and After Examples

Visual guide showing what Loppers does with various code structures.

## Python Examples

### Constructor with Docstring

**Before:**
```python
class Calculator:
    def __init__(self, name: str):
        """Initialize calculator."""
        self.name = name
        self._setup()
    
    def _setup(self):
        """Setup method."""
        self.ready = True
```

**After:**
```python
class Calculator:
    def __init__(self, name: str):
        """Initialize calculator."""
    
    def _setup(self):
        """Setup method."""
```

### Regular and Async Methods

**Before:**
```python
class Service:
    def process(self, data):
        """Process data."""
        result = []
        for item in data:
            result.append(item * 2)
        return result
    
    async def fetch(self):
        """Fetch data."""
        response = await client.get('/api')
        return response.json()
```

**After:**
```python
class Service:
    def process(self, data):
        """Process data."""
    
    async def fetch(self):
        """Fetch data."""
```

### Special Methods

**Before:**
```python
class User:
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return f"User({self.name})"
    
    @property
    def full_name(self):
        return self.first + " " + self.last
    
    @staticmethod
    def validate(value):
        return len(value) > 0
```

**After:**
```python
class User:
    def __init__(self, name):
    
    def __str__(self):
    
    @property
    def full_name(self):
    
    @staticmethod
    def validate(value):
```

---

## JavaScript / TypeScript Examples

### Constructor with Methods

**Before:**
```javascript
class UserService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.cache = {};
    }

    async getUser(id) {
        if (this.cache[id]) return this.cache[id];
        const user = await fetch(this.baseUrl + '/' + id);
        return user.json();
    }
}
```

**After:**
```javascript
class UserService {
    constructor(baseUrl) {
    }

    async getUser(id) {
    }
}
```

### Arrow Functions

**Before:**
```javascript
const handleClick = async (event) => {
    event.preventDefault();
    const data = await fetch('/api');
    console.log(data);
    return data;
};

const calculate = (a, b) => {
    const result = a + b;
    console.log(result);
    return result;
};
```

**After:**
```javascript
const handleClick = async (event) => {
};

const calculate = (a, b) => {
};
```

### Object Methods

**Before:**
```javascript
const api = {
    getUser: function(id) {
        return fetch('/api/users/' + id);
    },

    updateUser: async (id, data) => {
        return fetch('/api/users/' + id, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
};
```

**After:**
```javascript
const api = {
    getUser: function(id) {
    },

    updateUser: async (id, data) => {
    }
};
```

### Class with Mixed Methods

**Before:**
```javascript
class DataHandler {
    constructor(source) {
        this.source = source;
    }

    load() {
        const data = this.source.read();
        this.validate(data);
        return data;
    }

    validate = (data) => {
        if (!data) throw new Error('No data');
        return true;
    }

    async process() {
        const data = await this.load();
        return data.map(item => item * 2);
    }
}
```

**After:**
```javascript
class DataHandler {
    constructor(source) {
    }

    load() {
    }

    validate = (data) => {
    }

    async process() {
    }
}
```

---

## Java Examples

### Constructor and Methods

**Before:**
```java
public class UserService {
    private String baseUrl;
    
    public UserService(String baseUrl) {
        this.baseUrl = baseUrl;
        this.validate();
    }
    
    public User getUserById(String id) {
        Database db = new Database();
        return db.query(id);
    }

    private void validate() {
        if (baseUrl == null) {
            throw new IllegalArgumentException("BaseUrl required");
        }
    }
}
```

**After:**
```java
public class UserService {
    private String baseUrl;
    
    public UserService(String baseUrl) {
    }
    
    public User getUserById(String id) {
    }

    private void validate() {
    }
}
```

### With Annotations

**Before:**
```java
public class Repository {
    @Override
    public String toString() {
        return "Repository{}";
    }

    @Deprecated
    public void oldMethod() {
        System.out.println("old");
    }
}
```

**After:**
```java
public class Repository {
    @Override
    public String toString() {
    }

    @Deprecated
    public void oldMethod() {
    }
}
```

---

## Cases NOT Handled

### JavaScript Concise Arrow (no body to remove)

```javascript
// These are unchanged - they have no statement block
const add = (a, b) => a + b;
const double = x => x * 2;
```

### Python Lambda (no body to remove)

```python
# Lambdas are unchanged - they have no block to remove
add = lambda x, y: x + y
```

### JavaScript Getter/Setter (not yet supported)

```javascript
class User {
    get name() {
        return this._name;
    }
    
    set name(value) {
        this._name = value;
    }
}
```

---

## Summary Table

| Feature | Python | JS/TS | Java | Go | Rust | Other |
|---------|--------|-------|------|----|----|-------|
| Functions | ✅ | ✅ | - | ✅ | ✅ | ✅ |
| Async Functions | ✅ | ✅ | - | - | - | - |
| Methods | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Constructor | ✅ | ✅ | ✅ | - | ✅ | ✅ |
| Arrow Functions | - | ✅ | - | - | - | - |
| Docstrings | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Decorators | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Concise Arrows | - | ❌ | - | - | - | - |
| Lambda | ❌ | - | - | - | - | - |
| Getters/Setters | ❌ | ❌ | ❌ | - | - | - |
