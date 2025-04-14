import express from 'express';
import { validateInput } from '../middleware/inputValidator';
import { userRegisterSchema, userLoginSchema } from '../schemas/user';
import { registerUser, loginUser, getUserData, refreshUser, logoutUser } from '../controllers/user';

const userRouter = express.Router();
userRouter.post('/register', validateInput(userRegisterSchema), registerUser);
userRouter.post('/login', validateInput(userLoginSchema), loginUser);
userRouter.get('/data', getUserData);
userRouter.get('/refresh', refreshUser);
userRouter.get('/logout', logoutUser);

export default userRouter;
