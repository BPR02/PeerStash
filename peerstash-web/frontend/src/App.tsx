import React, { useEffect, useState } from 'react';
import axios from 'axios';

axios.defaults.withCredentials = true;
const BACKEND = `${process.env.WEB_APP_IP}:${process.env.WEB_APP_API_PORT}` || 'http://localhost:3001';

const App: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [token, setToken] = useState<string | null>(null);
  const [message, setMessage] = useState<string>('');
  const [rememberMe, setRememberMe] = useState<boolean>(false);

  const register = async () => {
    try {
      await axios.post(`${BACKEND}/user/register`, {
        username: username,
        email: email,
        password: password,
      });
      setMessage(`Registration successful!`);
    } catch {
      setMessage('Registration failed');
    }
  };

  const login = async () => {
    try {
      const res = await axios.post<{ accessToken: string }>(`${BACKEND}/user/login`, {
        email: email,
        password: password,
      });
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem('token', res.data.accessToken);
      setToken(res.data.accessToken);
      setMessage(`Login successful!`);
    } catch {
      setMessage('Login failed');
    }
  };

  const logout = () => {
    axios.get(`${BACKEND}/user/logout`);
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    setToken(null);
    setMessage('Logged out');
  };

  const refresh = async () => {
    try {
      const res = await axios.get<{ accessToken: string }>(
        `${BACKEND}/user/refresh`
      );
      localStorage.setItem('token', res.data.accessToken);
      setToken(res.data.accessToken);
      setMessage(`Refresh successful!`);
    } catch {
      setMessage('Refresh failed');
    }
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const getUserData = async () => {
    try {
      const res = await axios.get<{ message: string }>(`${BACKEND}/user/data`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessage(res.data.message);
    } catch {
      setMessage('Not authorized');
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Login</h2>
      <input
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <br />
      <input
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <br />
      <input
        placeholder="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <br />
      <button onClick={register}>Register</button>
      <button onClick={login}>Login</button>
      <br />
      <button onClick={getUserData} disabled={!token}>
        Get User Info
      </button>
      <button onClick={logout} disabled={!token}>Logout</button>
      <br />
      <label>
        <input
          type="checkbox"
          checked={rememberMe}
          onChange={(e) => setRememberMe(e.target.checked)}
        />
        Remember Me
      </label>
      <p>{message}</p>
      <br />
      <button onClick={refresh}>Refresh</button>
    </div>
  );
};

export default App;
