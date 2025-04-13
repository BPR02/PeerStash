import express from 'express';
import { connect } from '../controllers/test';

const rootRouter = express.Router();
rootRouter.get('/', connect);

export default rootRouter;
