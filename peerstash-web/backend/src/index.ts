import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import { errorHandler } from './middleware/errorHandler';
import userRouter from './routes/user';
import testRouter from './routes/test';
import dotenv from 'dotenv';
import { createUserTable } from './data/db';


const app = express();
const PORT = 3001;

// set up
dotenv.config();
createUserTable();

// middleware
app.use(cors({
  origin: `${process.env.WEB_APP_IP}:${process.env.WEB_APP_PORT}`,
  credentials: true,
  exposedHeaders: ["set-cookie"]
}));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(errorHandler);

// routes
app.use('/test', testRouter);
app.use('/user', userRouter);
app.use((_req: Request, res: Response, _next: NextFunction) => {
  res.status(404).send("Route not found")
});

// open server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
