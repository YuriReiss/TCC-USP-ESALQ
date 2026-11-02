/* eslint-disable @typescript-eslint/no-require-imports */
const express = require('express');
const router = express.Router();
const aiController = require('../controllers/aiController.js');

// A rota agora aponta para o novo nome da função e o caminho correto esperado pelo Python
router.post('/otimizar-portfolio', aiController.gerarPortfolioOtimizado);

module.exports = router;