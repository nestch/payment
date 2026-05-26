* ### TODO: migrar o rabbitmp para https://www.cloudamqp.com 
* ### TODO: testar o payment no railway
* ### TODO: resolver a criação do token


# Configuração do WhatsApp Business API na Zavu (Nestch)

## Estado atual

Você já:
- comprou um número na Zavu
- criou uma conta Meta/Facebook
- tentou criar o Business Manager
- recebeu o erro:

> "Sua conta do Facebook é muito nova para criar uma conta comercial"

---

# PASSO 1 — AGUARDAR A META LIBERAR A CONTA

A Meta bloqueia temporariamente contas recém-criadas para evitar spam e abuso.

## Tempo recomendado

- mínimo: 1 hora
- ideal: 12h a 24h

---

# PASSO 2 — PREPARAR A CONTA META

## 2.1 Confirmar email

Abra:

- [Facebook](https://www.facebook.com/)

Verifique:
- email confirmado
- nenhuma pendência

---

## 2.2 Confirmar telefone

Abra:

- [Central de contatos Meta](https://accountscenter.facebook.com/personal_info/contact_points)

Adicione:
- número de telefone real
- confirme via SMS

---

## 2.3 Ativar autenticação em 2 fatores

Abra:

- [Segurança Meta](https://accountscenter.facebook.com/password_and_security/two_factor)

Ative:
- app autenticador
ou
- SMS

---

## 2.4 Completar o perfil

Adicionar:
- foto de perfil
- nome real
- informações básicas

---

# PASSO 3 — NÃO TENTAR REPETIDAMENTE

Evite:
- ficar tentando criar Business Manager várias vezes
- usar VPN
- trocar IP
- criar múltiplas contas Meta

---

# PASSO 4 — CRIAR O BUSINESS MANAGER

Após aguardar algumas horas:

Abra:

- [Meta Business](https://business.facebook.com/)
- [Meta Business Overview](https://business.facebook.com/overview)

Faça login com a conta criada.

---

# PASSO 5 — CRIAR A EMPRESA

Quando aparecer:

- "Criar conta"
ou
- "Criar portfólio empresarial"

Clique.

---

# PASSO 6 — PREENCHER OS DADOS

## Nome da empresa

```text
Nestch
```

## Nome do administrador

Use:
- seu nome real

---

## Email empresarial

Exemplo:

```text
contato@nestch.com.br
```

---

# PASSO 7 — CONFIRMAR EMAIL DA META

A Meta enviará um email.

Clique em:
- "Confirmar agora"

---

# PASSO 8 — ABRIR AS CONFIGURAÇÕES DO NEGÓCIO

Abra:

- [Configurações do Business](https://business.facebook.com/settings)

---

# PASSO 9 — PREENCHER DADOS EMPRESARIAIS

Menu:

```text
Informações da empresa
```

Adicionar:
- telefone
- site
- endereço
- país

---

# PASSO 10 — ENTRAR NA ZAVU

Abrir:

- [Painel Zavu](https://app.zavu.dev/)

---

# PASSO 11 — CONFIGURAR WHATSAPP

No painel da Zavu procurar:

```text
Integrações
```

ou:

```text
WhatsApp
```

ou:

```text
Connect Meta
```

---

# PASSO 12 — CONECTAR À META

A Zavu abrirá o fluxo oficial da Meta.

Selecionar:
- Business Manager da Nestch

Criar:
- WhatsApp Business Account (WABA)

Vincular:
- número comprado na Zavu

---

# PASSO 13 — CONFIGURAR PERFIL DO WHATSAPP

## Nome exibido

Sugestões:

```text
Nestch
```

ou:

```text
Nestch Imóveis
```

---

## Categoria

```text
Imobiliária
```

ou:

```text
Real Estate
```

---

## Descrição

Exemplo:

```text
Plataforma imobiliária para compra, venda e aluguel de imóveis.
```

---

# PASSO 14 — AGUARDAR APROVAÇÃO

Após aprovação:
- o WhatsApp será habilitado
- o botão deixará de ficar cinza
- será possível enviar mensagens

---

# PASSO 15 — TESTAR ENVIO

Na Zavu:

```text
Testador de Mensagens
```

Selecionar:
- WhatsApp

Enviar:
- mensagem teste

---

# PASSO 16 — INTEGRAÇÃO COM SUA API FASTAPI

Depois da ativação você poderá:
- enviar mensagens automáticas
- receber webhooks
- criar atendimento automático
- enviar OTP
- confirmar visitas

---

# LINKS IMPORTANTES

## Meta Business

- [Abrir Meta Business](https://business.facebook.com/)

---

## Configurações do Business

- [Abrir Configurações](https://business.facebook.com/settings)

---

## Segurança Meta

- [Abrir Segurança Meta](https://accountscenter.facebook.com/password_and_security)

---

## Contatos Meta

- [Abrir Central de Contatos](https://accountscenter.facebook.com/personal_info/contact_points)

---

## Painel Zavu

- [Abrir Painel Zavu](https://app.zavu.dev/)

---

## Documentação Zavu

- [Abrir Documentação](https://docs.zavu.dev/)