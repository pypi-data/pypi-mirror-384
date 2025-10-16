import React, { useState, useEffect } from 'react';

interface User {
    id: string;
    name: string;
}

async function fetchUser(id: string): Promise<User> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

export const UserComponent: React.FC<{ id: string }> = ({ id }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const loadUser = async () => {
            const userData = await fetchUser(id);
            setUser(userData);
            setLoading(false);
        };
        loadUser();
    }, [id]);

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>{user?.name}</h1>
        </div>
    );
};
