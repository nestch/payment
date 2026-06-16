# Guia de Testes — Simulação de Pagamentos (branch `simulate`)

Base URL: `http://localhost:8000`

---

## Pré-requisito: obter um JWT

Todos os endpoints exigem `Authorization: Bearer <token>`.

```bash
curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "expires_in_minutes": 60}' | jq .
```

Resposta esperada:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_at": "..."
}
```

Exporte o token para reutilizar nos demais comandos:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "expires_in_minutes": 60}' | jq -r .access_token)
```

---

## Pacotes de crédito disponíveis

| credits | amount (BRL) |
|---------|-------------|
| 10.00   | R$ 10,00    |
| 15.00   | R$ 15,00    |
| 20.00   | R$ 20,00    |
| 30.00   | R$ 30,00    |
| 40.00   | R$ 40,00    |
| 50.00   | R$ 50,00    |

---

## Endpoint 1 — `POST /simulate/checkout`

Cria o pagamento (PENDING + PIX) e aplica o desfecho **em uma única chamada**.

### Cenário 1 — Sucesso (CONFIRMED)

```bash
curl -s -X POST http://localhost:8000/simulate/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "credits": 20.00, "simulate": "success"}' | jq .
```

Resposta esperada:
```json
{
  "payment_id": 1,
  "status": "CONFIRMED",
  "simulated_event": "checkout.session.completed",
  "transaction_id": "sim_pix_<hex>"
}
```

O que deve ter ocorrido no banco:
- `paymentsTable`: `status=CONFIRMED`, `credited_at` preenchido, `transaction_id=sim_pix_*`
- `creditsLedger`: nova linha com `credits=20.00`, `stripe_event_id=sim_evt_*`
- `userTable`: `credit` incrementado em `20.00`

---

### Cenário 2 — Falha (FAILED)

```bash
curl -s -X POST http://localhost:8000/simulate/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "credits": 20.00, "simulate": "failure"}' | jq .
```

Resposta esperada:
```json
{
  "payment_id": 2,
  "status": "FAILED",
  "simulated_event": "checkout.session.async_payment_failed",
  "transaction_id": null
}
```

O que deve ter ocorrido no banco:
- `paymentsTable`: `status=FAILED`, `credited_at=NULL`, `transaction_id=NULL`
- `creditsLedger`: nenhuma linha inserida
- `userTable`: crédito **não** alterado

---

### Cenário 3 — Cancelamento (CANCELED)

```bash
curl -s -X POST http://localhost:8000/simulate/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "credits": 20.00, "simulate": "cancel"}' | jq .
```

Resposta esperada:
```json
{
  "payment_id": 3,
  "status": "CANCELED",
  "simulated_event": "checkout.session.expired",
  "transaction_id": null
}
```

O que deve ter ocorrido no banco:
- `paymentsTable`: `status=CANCELED`, sem créditos
- `creditsLedger`: nenhuma linha inserida
- `userTable`: crédito **não** alterado

---

### Cenário 4 — Pacote de crédito inválido (erro 400)

```bash
curl -s -X POST http://localhost:8000/simulate/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "credits": 99.00, "simulate": "success"}' | jq .
```

Resposta esperada:
```json
{
  "detail": "Unsupported credits package: 99.00"
}
```
HTTP Status: `400 Bad Request`

---

### Cenário 5 — Sem token (erro 401)

```bash
curl -s -X POST http://localhost:8000/simulate/checkout \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "credits": 20.00, "simulate": "success"}' | jq .
```

Resposta esperada:
```json
{
  "detail": "Missing bearer token"
}
```
HTTP Status: `401 Unauthorized`

---

## Endpoint 2 — `POST /simulate/callback`

Aplica um desfecho sobre um Payment **já existente em PENDING**. Útil para simular a progressão em etapas.

### Fluxo em duas etapas

**Passo 1** — Criar o pagamento (sem aplicar desfecho ainda):

> Não há endpoint para criar apenas o PENDING via simulate. Use `/simulate/checkout` com `simulate=success` e anote o `payment_id`, ou crie via `/payments/stripe/checkout` (que usa Stripe real). Para simular somente PENDING + callback separado, chame `/simulate/checkout` com `simulate=failure` ou `cancel` e o status já está terminal — não é possível. **O fluxo de duas etapas funciona assim:**

```bash
# Cria PENDING e aplica 'failure' para ter um payment no banco
# Para ter um PENDING puro e depois callback, primeiro crie via checkout com um simulate qualquer
# e use um payment_id que ainda esteja PENDING (ex.: reinicie o banco ou use um ID ainda não processado)
```

> **Nota:** como `/simulate/checkout` aplica o desfecho imediatamente, para testar o `/simulate/callback` de forma isolada use o banco diretamente para inserir um PENDING, ou teste com um `payment_id` criado por outro meio.

---

### Cenário 6 — Callback de sucesso em PENDING existente

```bash
curl -s -X POST http://localhost:8000/simulate/callback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_id": 1, "simulate": "success"}' | jq .
```

Resposta esperada (payment_id 1 em PENDING):
```json
{
  "payment_id": 1,
  "status": "CONFIRMED",
  "simulated_event": "checkout.session.completed"
}
```

---

### Cenário 7 — Callback em payment já em status terminal (erro 409)

Tenta aplicar desfecho em um payment que já é CONFIRMED, FAILED ou CANCELED:

```bash
curl -s -X POST http://localhost:8000/simulate/callback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_id": 1, "simulate": "success"}' | jq .
```

Resposta esperada (quando payment_id 1 já é CONFIRMED):
```json
{
  "detail": "Payment already in terminal status: CONFIRMED"
}
```
HTTP Status: `409 Conflict`

---

### Cenário 8 — Callback em payment inexistente (erro 404)

```bash
curl -s -X POST http://localhost:8000/simulate/callback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_id": 99999, "simulate": "success"}' | jq .
```

Resposta esperada:
```json
{
  "detail": "Payment not found"
}
```
HTTP Status: `404 Not Found`

---

## Verificação no banco

Conecte ao MySQL para confirmar os efeitos colaterais:

```bash
sudo docker exec -it payment-db-1 mysql -u payments -ppayments payments
```

```sql
-- Ver todos os pagamentos simulados
SELECT id, user_id, amount, credits, status, method, transaction_id, credited_at
FROM paymentsTable
ORDER BY id DESC
LIMIT 10;

-- Ver o ledger de créditos
SELECT id, user_id, payment_id, credits, amount_paid, stripe_event_id, created_at
FROM creditsLedger
ORDER BY id DESC
LIMIT 10;

-- Ver saldo de créditos do usuário
SELECT userID, credit
FROM userTable
WHERE userID = 1;
```

---

## Verificação de idempotência (Cenário 9)

O `INSERT IGNORE` garante que um mesmo `payment_id` não gera duas linhas no `creditsLedger`.
Para verificar, tente confirmar via callback um payment que já tem `credited_at` preenchido — o endpoint retornará `409` pois o status já é terminal.

Para testar a guard do `credited_at` diretamente:

```sql
-- Zera credited_at de um payment CONFIRMED para forçar re-execução
UPDATE paymentsTable SET status='PENDING', credited_at=NULL WHERE id = 1;
```

Em seguida chame `/simulate/callback` com `simulate=success` duas vezes.
A segunda chamada retornará `409` (status já CONFIRMED após a primeira).
No `creditsLedger`, haverá **exatamente uma linha** para aquele `payment_id`.

---

## Resumo dos cenários

| # | Endpoint           | simulate  | Resultado esperado         | HTTP |
|---|--------------------|-----------|----------------------------|------|
| 1 | `/simulate/checkout` | `success` | CONFIRMED + ledger + crédito | 200 |
| 2 | `/simulate/checkout` | `failure` | FAILED, sem ledger         | 200  |
| 3 | `/simulate/checkout` | `cancel`  | CANCELED, sem ledger       | 200  |
| 4 | `/simulate/checkout` | `success` (credits=99) | Erro pacote inválido | 400 |
| 5 | `/simulate/checkout` | (sem JWT) | Não autorizado             | 401  |
| 6 | `/simulate/callback` | `success` | CONFIRMED em PENDING existente | 200 |
| 7 | `/simulate/callback` | `success` | Payment já terminal        | 409  |
| 8 | `/simulate/callback` | `success` | Payment não encontrado     | 404  |
| 9 | idempotência       | `success` x2 | Apenas 1 linha no ledger | 409 na 2ª |
