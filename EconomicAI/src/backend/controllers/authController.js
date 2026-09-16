/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require('fs');
const path = require('path');

// Usa path.join para garantir que o arquivo seja encontrado independente de onde o servidor for iniciado
const dataPath = path.join(__dirname, '../data/usuarios.json');

const login = (req, res) => {
  const { email, senha } = req.body;

  const data = fs.readFileSync(dataPath, 'utf8');
  const usuarios = JSON.parse(data);

  const usuarioValido = usuarios.find(u => u.email === email && u.senha === senha);

  if (usuarioValido) {
    res.status(200).json({ token: 'fake-jwt-token-12345' });
  } else {
    res.status(401).json({ message: 'Credenciais inválidas' });
  }
};

module.exports = {
  login
};