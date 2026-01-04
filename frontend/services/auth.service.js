import api from './api';

export const authService = {
  login: async (email, password) => {
    // const response = await api.post('/auth/login', { email, password });
    // return response.data;
    return { 
      user: { name: 'Demo User', email }, 
      token: 'demo-token',
      is_setup_completed: true 
    };
  },

  register: async (name, email, password) => {
    // const response = await api.post('/auth/register', { name, email, password });
    // return response.data;
    return { 
      user: { name, email }, 
      token: 'demo-token',
      is_setup_completed: false 
    };
  },

  logout: async () => {
    // await api.post('/auth/logout');
    return true;
  },

  getCurrentUser: async () => {
    // const response = await api.get('/auth/me');
    // return response.data;
    // Simulate a delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return { 
      name: 'Demo User', 
      email: 'demo@example.com',
      is_setup_completed: true
    };
  },
};
