CREATE TABLE IF NOT EXISTS `paymentsTable` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `userID` BIGINT NOT NULL,
  `amount` DECIMAL(10,2) NOT NULL,
  `currency` VARCHAR(3) NOT NULL DEFAULT 'BRL',
  `credits` DECIMAL(10,2) NULL,
  `status` ENUM('PENDING','CONFIRMED','FAILED','CANCELED') NOT NULL DEFAULT 'PENDING',
  `method` ENUM('CREDIT_CARD','PIX','BOLETO','PAYPAL') NOT NULL,
  `transaction_id` VARCHAR(100) NULL,
  `idempotency_key` VARCHAR(64) NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `credited_at` DATETIME(6) NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_payments_transaction_id` (`transaction_id`),
  UNIQUE KEY `uq_payments_idempotency_key` (`idempotency_key`),
  KEY `ix_payments_userID` (`userID`),
  KEY `ix_payments_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `creditsLedger` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `userID` BIGINT NOT NULL,
  `payment_id` BIGINT NOT NULL,
  `credits` DECIMAL(10,2) NOT NULL,
  `amount_paid` DECIMAL(10,2) NOT NULL,
  `stripe_event_id` VARCHAR(255) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_credits_ledger_payment_id` (`payment_id`),
  KEY `ix_credits_ledger_userID` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
