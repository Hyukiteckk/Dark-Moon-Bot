# 📁 Estrutura Modular - Dark Moon Bot

## 🎯 Organização do Projeto

```
Dark-Moon-Bot/
├── IA.py                          # 🎛️ Arquivo Principal (Startup, Event Handlers)
├── utils.py                       # 🔧 Funções Compartilhadas (APIs, Pontos, etc)
├── requirements.txt               # 📦 Dependências
├── .env.example                   # 🔑 Exemplo de variáveis
├── .env                          # 🔑 Variáveis de ambiente (não commitado)
│
├── commands/                      # 📂 Pasta com todos os Comandos
│   ├── __init__.py               # 📋 Importa todos os módulos
│   ├── pontos.py                 # 💰 Pontos, Ranking, Stats
│   ├── moderacao.py              # 🔨 Kick, Ban, Mute, Limpar Chat
│   ├── imagens.py                # 🎨 Gerar Imagens (Imaginar/Desenhar)
│   ├── clima.py                  # ☀️ Clima, Tradução, Server Info
│   ├── ia.py                     # 🤖 IA, Modo Agressivo, Regras
│   └── carro.py                  # 🚗 Sistema do Carro (Botão + Loop)
│
└── .vscode/                       # ⚙️ Configuração do VS Code
    └── launch.json
```

## 📦 O que cada arquivo faz

### **IA.py** - Arquivo Principal
- ✅ Configuração inicial (Discord intents, client, tree)
- ✅ Event Handlers (`on_ready`, `on_member_join`, `on_voice_state_update`, `on_message`)
- ✅ Slash Commands (`/badge`, `/carro`)
- ✅ Roteamento de mensagens para os comandos corretos

### **utils.py** - Funções Compartilhadas
- ✅ **Gerenciamento de Pontos**: `load_points()`, `save_points()`, `add_user_points()`, `get_user_points()`
- ✅ **Sessões de Voz**: `start_voice_session()`, `stop_voice_session()`, `update_current_voice_sessions()`
- ✅ **APIs**: `get_weather()`, `perform_google_search()`, `call_groq()`
- ✅ **Busca de Membros**: `get_member()`

### **commands/pontos.py** - Sistema de Pontos
- 📊 `cmd_zerar_pontos()` - Zera ranking (admin)
- 📊 `cmd_meus_pontos()` - Mostra seus pontos
- 📊 `cmd_ranking()` - Top 10 do servidor
- 📊 `setup_pontos_commands()` - Router para esses comandos

### **commands/moderacao.py** - Moderação
- 🔨 `cmd_mute()` - Muta membro
- 🔨 `cmd_unmute()` - Desmuta membro
- 🔨 `cmd_kick()` - Remove da call
- 🔨 `cmd_ban()` - Bane membro
- 🔨 `cmd_limpar_chat()` - Apaga mensagens
- 🔨 `cmd_linguicar()` - Easter egg
- 🔨 `setup_moderacao_commands()` - Router

### **commands/imagens.py** - Geração de Imagens
- 🎨 `cmd_imaginar()` - Gera imagem com IA
- 🎨 `setup_imagens_commands()` - Router

### **commands/clima.py** - Clima, Tradução e Info
- ☀️ `cmd_climate()` - Busca clima
- ☀️ `cmd_traduzir()` - Traduz textos
- ☀️ `cmd_serverinfo()` - Info do servidor
- ☀️ `setup_clima_commands()` - Router

### **commands/ia.py** - Inteligência Artificial
- 🤖 `cmd_ia_response()` - Resposta com IA e busca web
- 🤖 `cmd_modo_agressivo()` - Ativa modo agressivo
- 🤖 `cmd_modo_normal()` - Desativa modo agressivo
- 🤖 `cmd_limpar_memoria()` - Limpa histórico
- 🤖 `cmd_regras()` - Mostra regras
- 🤖 `setup_ia_commands()` - Router

### **commands/carro.py** - Sistema do Carro
- 🚗 `CarroView` - Classe do botão do carro
- 🚗 `spawn_carro_func()` - Gera carro no canal
- 🚗 `carro_background_loop()` - Loop automático (4 em 4h)
- 🚗 `carro_loop_with_delay()` - Helper para forçar carro

## 🔄 Fluxo de Funcionamento

```
IA.py (on_message)
    ↓
route_command() - Roteia para o módulo correto
    ↓
    ├─→ setup_pontos_commands()  [commands/pontos.py]
    ├─→ setup_moderacao_commands()  [commands/moderacao.py]
    ├─→ setup_imagens_commands()  [commands/imagens.py]
    ├─→ setup_clima_commands()  [commands/clima.py]
    └─→ setup_ia_commands()  [commands/ia.py]
```

## ✨ Benefícios da Estrutura Modular

| Benefício | Descrição |
|-----------|-----------|
| 📦 **Modularidade** | Cada arquivo = Uma responsabilidade |
| 🧹 **Limpeza** | IA.py enxuto, apenas 200 linhas |
| 🔧 **Manutenção** | Fácil encontrar e editar funcionalidades |
| 👥 **Colaboração** | Múltiplas pessoas em arquivos diferentes |
| 🧪 **Testes** | Importa apenas o que precisa testar |
| 📈 **Escalabilidade** | Adiciona novos comandos sem bagunça |

## 🚀 Como Adicionar um Novo Comando

### 1. Criar novo arquivo em `commands/novo_comando.py`

```python
# commands/novo_comando.py

async def cmd_novo(message: discord.Message):
    """Novo comando"""
    await message.channel.send("Olá!")

async def setup_novo_comando(client, message: discord.Message):
    """Router para o novo comando"""
    lc = message.content.lower()
    
    if lc == "novo":
        await cmd_novo(message)
        return True
    
    return False
```

### 2. Importar em `commands/__init__.py`

```python
from .novo_comando import setup_novo_comando

__all__ = [
    # ... outros
    "setup_novo_comando",
]
```

### 3. Importar em `IA.py`

```python
from commands.novo_comando import setup_novo_comando
```

### 4. Adicionar ao router em `route_command()`

```python
async def route_command(message: discord.Message, channel_id: int) -> bool:
    # ... outros
    
    if await setup_novo_comando(client, message):
        return True
    
    return False
```

## 🔐 Boas Práticas

✅ **Sempre use funções em `utils.py` que são compartilhadas**
✅ **Cada comando é uma função async separada**
✅ **Use docstrings para documentar funções**
✅ **Imports organizados no início do arquivo**
✅ **Nomes descritivos para funções e variáveis**

---

**Criado em:** 27/01/2026
**Version:** 2.0 (Modularizado)
**Autor:** Dark Moon System
