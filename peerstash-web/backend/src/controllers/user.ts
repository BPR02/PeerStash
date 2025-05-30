import { Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { StatusCodes } from 'http-status-codes';
import { pool } from '../data/db';
import dotenv from 'dotenv';
dotenv.config();

// Generate tokens
const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET || 'jwt-access-secret-super-secret-secret';
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'jwt-refresh-secret-super-secret-secret';

const generateAccessToken = (email: string) =>
  jwt.sign({ email }, ACCESS_SECRET, { expiresIn: '15m' });

const generateRefreshToken = (email: string) =>
  jwt.sign({ email }, REFRESH_SECRET, { expiresIn: '30d' });






export const registerUser = async (req: Request, res: Response) => {
  // Handle user registration logic using validated data from req.body
  const { username, email, password } = req.body;

  const password_hash = bcrypt.hashSync(password, 10);
  const queryText = `INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3);`;
  const values = [username, email, password_hash];
  try { 
    await pool.query(queryText, values);
  } catch (error) {
    console.log(error);
    return res.status(StatusCodes.INTERNAL_SERVER_ERROR).json({ error });
  }

  return res.status(StatusCodes.OK).json({ message: `Registered ${username}`});
};

export const loginUser = async (req: Request, res: Response) => {
  // Handle user login logic using validated data from req.body
  const { email, password } = req.body;

  try {
    const passwordMatch = await pool.query(
      `SELECT password_hash FROM users WHERE email = $1;`,
      [email]
    );
    const userPasswordHash: string = passwordMatch.rows[0].password_hash;
    if (!bcrypt.compareSync(password, userPasswordHash)) {
      return res.status(StatusCodes.UNAUTHORIZED).json({ message: 'Invalid credentials'});
    }
  } catch (err) {
    console.log(err);
    return res.status(StatusCodes.INTERNAL_SERVER_ERROR).json({ error: err });
  }
  
  const accessToken = generateAccessToken(email);
  const refreshToken = generateRefreshToken(email);

  // Send refresh token as HTTP-only cookie
  res.cookie('refreshToken', refreshToken, {
    httpOnly: true,
    secure: false, // set true if using HTTPS
    path: '/user/refresh',
    sameSite: 'lax',
  });

  return res.status(StatusCodes.OK).json({ accessToken });
};

export const getUserData = (_req: Request, res: Response) => {
  return res.status(StatusCodes.OK).json({ message: 'User Data not Implemented' });
};

export const refreshUser = (req: Request, res: Response) => {
  const token = req.cookies.refreshToken;
  if (!token) return res.sendStatus(StatusCodes.UNAUTHORIZED);

  jwt.verify(token, REFRESH_SECRET, (err: any, user: any) => {
    if (err) return res.sendStatus(StatusCodes.FORBIDDEN);

    const newAccessToken = generateAccessToken(user.username);
    res.status(StatusCodes.OK).json({ accessToken: newAccessToken });
  });
}

export const logoutUser = (_req: Request, res: Response) => {
  res.clearCookie('refreshToken', { path: '/user/refresh' });
  res.status(StatusCodes.OK).json({ message: 'Logged out' });
}
