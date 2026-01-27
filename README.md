# 🌙 Dark Moon Bot

Um bot Discord completo e modular com inteligência artificial, sistema de pontos, moderação, geração de imagens e muito mais!

## ✨ Features

### 🤖 Inteligência Artificial
- Respostas inteligentes com busca na web integrada
- Modo agressivo configurável
- Gerenciamento de memória de conversa
- Integração com Groq API

### 💰 Sistema de Pontos
- Pontos por tempo em call de voz
- Ranking em tempo real
- Estatísticas de usuário
- Gerenciamento de pontos (admin)

### 🔨 Moderação
- Mute/Unmute de membros
- Kick de membros
- Ban de usuários
- Limpeza de chat em massa
- Easter eggs

### 🎨 Criatividade
- Geração de imagens com IA
- Comando `/imaginar` para criar imagens

### 🌤️ Informações
- Consulta de clima em tempo real
- Tradutor de textos
- Informações do servidor
- Sistema automático de carro (4h em 4h)

### 🚗 Sistema do Carro
- Spawns automáticos de carro no canal
- Sistema de botões interativo
- Loop configurável

## 📋 Pré-requisitos

- Python 3.8+
- Conta Discord
- Token do bot Discord
- Chaves de API (OpenWeather, Groq)

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/Hyukiteckk/Dark-Moon-Bot.git
cd Dark-Moon-Bot
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto (copie do `.env.example`):

```env
# Discord
TOKEN=seu_token_aqui
APPLICATION_ID=seu_application_id
PUBLIC_KEY=sua_public_key

# Canais
ALLOWED_CHANNEL_ID=id_do_canal_permitido

# APIs
OPENWEATHER_API_KEY=sua_chave_openweather
GROQ_API_KEY=sua_chave_groq
GROQ_MODEL=model_groq_desejado
```

### 5. Execute o bot
```bash
python IA.py
```

## 📁 Estrutura do Projeto

```
Dark-Moon-Bot/
├── IA.py                    # 🎛️ Arquivo Principal (Event Handlers)
├── utils.py                 # 🔧 Funções Compartilhadas
├── requirements.txt         # 📦 Dependências
├── .env.example             # 🔑 Exemplo de variáveis
├── ESTRUTURA.md             # 📖 Documentação da arquitetura
│
├── commands/                # 📂 Comandos Modularizados
│   ├── pontos.py            # 💰 Pontos e Ranking
│   ├── moderacao.py         # 🔨 Moderação
│   ├── imagens.py           # 🎨 Geração de Imagens
│   ├── clima.py             # ☀️ Clima e Informações
│   ├── ia.py                # 🤖 IA e Respostas
│   └── carro.py             # 🚗 Sistema do Carro
│
└── .vscode/                 # ⚙️ Configuração VS Code
    └── launch.json
```

## 🎮 Comandos Disponíveis

### Pontos
- `/meus_pontos` - Ver seus pontos
- `/ranking` - Top 10 do servidor
- `/zerar_pontos` - Resetar ranking (admin)

### Moderação
- `/mute @usuario tempo` - Mutar usuário
- `/unmute @usuario` - Desmutar usuário
- `/kick @usuario` - Remover da call
- `/ban @usuario` - Banir usuário
- `/limpar_chat numero` - Deletar mensagens

### IA
- `/ia sua_pergunta` - Fazer pergunta com busca web
- `/modo_agressivo` - Ativar modo agressivo
- `/modo_normal` - Desativar modo agressivo
- `/limpar_memoria` - Limpar histórico de conversa
- `/regras` - Ver regras da IA

### Criatividade
- `/imaginar descricao` - Gerar imagem com IA

### Informações
- `/clima cidade` - Consultar clima
- `/traduzir texto` - Traduzir texto
- `/serverinfo` - Informações do servidor

## 🔑 Variáveis de Ambiente

| Variável | Descrição | Obrigatório |
|----------|-----------|-----------|
| `TOKEN` | Token do bot Discord | ✅ |
| `APPLICATION_ID` | ID da aplicação Discord | ✅ |
| `PUBLIC_KEY` | Public key da aplicação | ✅ |
| `ALLOWED_CHANNEL_ID` | ID do canal permitido | ✅ |
| `OPENWEATHER_API_KEY` | Chave OpenWeather API | ✅ |
| `GROQ_API_KEY` | Chave Groq API | ✅ |
| `GROQ_MODEL` | Modelo Groq a usar | ✅ |

## 🏗️ Arquitetura Modular

O projeto utiliza uma arquitetura modular onde cada funcionalidade é isolada em seu próprio arquivo:

```
IA.py (on_message)
    ↓
route_command()
    ├─→ pontos.py
    ├─→ moderacao.py
    ├─→ imagens.py
    ├─→ clima.py
    └─→ ia.py
```

**Benefícios:**
- 📦 Modularidade e responsabilidade única
- 🧹 Código limpo e organizado
- 🔧 Manutenção facilitada
- 👥 Colaboração entre desenvolvedores

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 👨‍💻 Autor

**Hyukiteckk** - [@Hyukiteckk](https://github.com/Hyukiteckk)

## 📞 Suporte

Para suporte, abra uma issue no repositório ou entre em contato.

---

**Feito por Hyukiteckk**
