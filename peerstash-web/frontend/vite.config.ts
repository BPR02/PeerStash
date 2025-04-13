import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import dotenv from 'dotenv';

dotenv.config();
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    host: true,
    origin: "http://0.0.0.0:3000"
  },
  define: {
    'process.env': process.env
  }
});
