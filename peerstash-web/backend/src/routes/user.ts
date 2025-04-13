import express from 'express';
import { validateInput } from '../middleware/inputValidator';
import { userRegisterSchema, userLoginSchema } from '../schemas/user';
import { registerUser, loginUser, getUserData } from '../controllers/user';

const userRouter = express.Router();
userRouter.post('/register', validateInput(userRegisterSchema), registerUser);
userRouter.post('/login', validateInput(userLoginSchema), loginUser);
userRouter.get('/data', getUserData);

export default userRouter;
