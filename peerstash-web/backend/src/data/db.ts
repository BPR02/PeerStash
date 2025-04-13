import pkg from 'pg';
import dotenv from 'dotenv';
const { Pool } = pkg;
dotenv.config();

export const pool = new Pool({
  user: process.env.POSTGRES_USER,
  host: process.env.POSTGRES_HOSTNAME,
  database: process.env.POSTGRES_DATABASE,
  password: process.env.POSTGRES_PASSWORD,
  port: 5432,
});

export const createUserTable = async () => {
  const queryText = `
    CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
    )
    `;

  try {
    pool.query(queryText);
    console.log("User table created if not exists");
  } catch (error) {
    console.log("Error creating users table : ", error);
  }
};
