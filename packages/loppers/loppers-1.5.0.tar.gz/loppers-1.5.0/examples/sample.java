public interface IUserRepository {
    User findById(String id);
    void save(User user);
}

public interface ILogger {
    void info(String message);
    void error(String message, Exception e);
}

public class UserService implements IUserRepository {
    private String baseUrl;
    private ILogger logger;

    public UserService(String baseUrl) {
        this.baseUrl = baseUrl;
        this.validate();
    }

    public User getUserById(String id) {
        Database db = new Database();
        return db.query(id);
    }

    public void updateUser(User user) {
        db.save(user);
        logger.info("User updated");
    }

    @Override
    public User findById(String id) {
        return getUserById(id);
    }

    @Override
    public void save(User user) {
        updateUser(user);
    }

    private void validate() {
        if (baseUrl == null) {
            throw new IllegalArgumentException("BaseUrl cannot be null");
        }
    }
}
