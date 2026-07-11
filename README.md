# 💼 Carteira de Investimentos

Sistema web para controle de carteira de investimentos, inspirado no KINVO.
Projeto de estudo desenvolvido durante meu curso de Python.

🌐 **Ao vivo:** [fredhansen.pythonanywhere.com](https://fredhansen.pythonanywhere.com)

## 🎯 Funcionalidades

- ✅ Cadastro, edição e exclusão de ativos (ações, FIIs, ETFs, renda fixa e **Tesouro Direto**)
- ✅ Registro de transações de compra e venda e de **proventos** (dividendos, JCP, rendimentos)
- ✅ Cotações via yfinance e Tesouro Transparente (fonte oficial), com cache
- ✅ Posição por ativo (quantidade, preço médio, custo) calculada a partir das transações
- ✅ Rentabilidade pelo **método de cotas** (como fundos de investimento), incluindo proventos
- ✅ Comparação histórica com **IBOV e CDI** (API do Banco Central), base 100
- ✅ Gráficos interativos com Plotly (alocação, evolução vs. benchmarks, patrimônio)
- ✅ Página de detalhe por ativo com **médias móveis e RSI**
- ✅ **Análise de risco**: volatilidade, drawdown máximo e correlação entre ativos
- ✅ **Login com senha criptografada** (Flask-Login)
- ✅ Interface moderna e responsiva: tema claro/escuro, ícones, fonte Inter e feedback ao usuário

## 🛠️ Tecnologias

- **Python 3.14** — linguagem principal
- **Flask** — framework web
- **Flask-Login** — autenticação
- **SQLAlchemy + SQLite** — banco de dados
- **yfinance** — cotações do mercado
- **Pandas** — manipulação de dados
- **Plotly** — gráficos interativos
- **Bootstrap 5** — interface

## 🚀 Como executar

1. Clone o repositório:
   ```
   git clone https://github.com/fredhansenads/SantusPYF.git
   cd SantusPYF
   ```
2. Crie e ative o ambiente virtual (Windows):
   ```
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Rode a aplicação:
   ```
   python app.py
   ```
5. Acesse `http://127.0.0.1:5000` no navegador.

O banco de dados SQLite é criado automaticamente na primeira execução (pasta `instance/`).

## 📚 Aprendizados

Este projeto faz parte da minha jornada de aprendizagem em Python.
Cada etapa foi construída passo a passo: rotas Flask, modelagem de dados
com ORM, templates Jinja2, formulários HTML, integração com API de cotações,
cálculos financeiros com pandas, cache, tratamento de erros e versionamento com Git.

## 👤 Autor

Fred Hansen — [GitHub](https://github.com/fredhansenads)
