interface User {
    id: string;
    name: string;
    email?: string;
}

interface IUserService {
    getAll(): Promise<User[]>;
    findById(id: string): Promise<User | undefined>;
}

type UserResponse = {
    data: User[];
    total: number;
};

async function fetchUser(id: string): Promise<User> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

const getUserById = async (id: string): Promise<User> => {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
};

class UserService implements IUserService {
    private baseUrl: string;
    private cache: Map<string, User>;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.cache = new Map();
    }

    async getAll(): Promise<User[]> {
        const users = await fetch(this.baseUrl + '/users');
        return users.json();
    }

    async findById(id: string): Promise<User | undefined> {
        return this.cache.get(id);
    }

    private validateUser(user: User): boolean {
        return !!user.id && !!user.name;
    }
}
