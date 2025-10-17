function fetchUser(id) {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

const getUserById = async (id) => {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
};

class BaseService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint) {
        const response = await fetch(this.baseUrl + endpoint);
        return response.json();
    }
}

class UserService extends BaseService {
    constructor(baseUrl) {
        super(baseUrl);
        this.cache = {};
    }

    async getAll() {
        const users = await this.request('/users');
        return users;
    }

    async findById(id) {
        return this.cache[id] || (await this.request(`/users/${id}`));
    }

    async create(userData) {
        const response = await fetch(this.baseUrl + '/users', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        return response.json();
    }
}

const userApi = {
    getUser: function(id) {
        return fetch(`/api/users/${id}`);
    },
    updateUser: async (id, data) => {
        return fetch(`/api/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    deleteUser: function(id) {
        return fetch(`/api/users/${id}`, { method: 'DELETE' });
    }
};
