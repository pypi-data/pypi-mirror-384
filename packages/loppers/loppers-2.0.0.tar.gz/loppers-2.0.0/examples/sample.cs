public interface IUserValidator {
    bool Validate(User user);
    string GetErrorMessage();
}

public class User {
    public string Id { get; set; }
    public string Name { get; set; }

    public int Age {
        get { return _age; }
        set { _age = value; }
    }
}

public class UserService : IUserValidator {
    public string Name { get; set; }

    public int Age {
        get { return _age; }
        set { _age = value; }
    }

    public void Process() {
        var squared = items.Select(x => x * x);
        var callback = delegate(int x) { return x + 1; };
        local_function();
    }

    public bool Validate(User user) {
        return !string.IsNullOrEmpty(user.Name) && user.Age > 0;
    }

    public string GetErrorMessage() {
        return "Validation failed";
    }

    private int local_function() {
        return 42;
    }
}
