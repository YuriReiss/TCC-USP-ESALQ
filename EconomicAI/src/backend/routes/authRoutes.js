/* eslint-disable @typescript-eslint/no-require-imports */
const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

// Cria a rota POST para o login
router.post('/login', authController.login);

module.exports = router;