/* eslint-disable @typescript-eslint/no-require-imports */
const express = require('express');
const router = express.Router();
const aiController = require('../controllers/aiController');

// Cria a rota POST para o chat
router.post('/chat', aiController.processarChat);

module.exports = router;    