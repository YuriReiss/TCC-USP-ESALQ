/* eslint-disable @typescript-eslint/no-require-imports */
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/authRoutes');
const aiRoutes = require('./routes/aiRoutes');

const app = express();

app.use(cors());
app.use(express.json());

// Registra o grupo de rotas de autenticação sob o prefixo /api/auth
app.use('/api/auth', authRoutes);
app.use('/api/ai', aiRoutes);

app.listen(3000, () => {
  console.log('API rodando em http://localhost:3000');
});