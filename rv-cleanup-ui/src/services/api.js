import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8001',// or your backend server/domain
});

export default api;