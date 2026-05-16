# Payments API

## Subir stack (dev)

1. Copie `.env.example` para `.env` e ajuste se necessário.
2. Suba os serviços:

```bash
bash scripts/start.sh
```

API: `http://localhost:8000`
RabbitMQ Management: `http://localhost:15672` (user/pass: `payments/payments`)

## Criar banco / rodar migrations

```bash
bash scripts/create_db.sh
```

## Endpoints

- `GET /health`
- `GET /ready`
- `POST /payments` (JWT obrigatório)
- `GET /payments/{id}` (JWT obrigatório)

## Worker

O worker é iniciado via docker-compose no serviço `worker` e consome a fila `payments.requested.q`.

## JWT

A API valida JWT via header `Authorization: Bearer <token>` usando `JWT_SECRET` e `JWT_ALGORITHM`.
