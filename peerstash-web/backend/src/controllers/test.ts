import { Request, Response } from 'express';
import { pool } from '../data/db';
import { StatusCodes } from 'http-status-codes';

export const connect = async (req: Request, res: Response) => {
  const result = await pool.query("SELECT current_database()");
  console.log("result", result.rows);
  return res.status(StatusCodes.OK).json({ message: `The database name is '${result.rows[0].current_database}'` });
};
