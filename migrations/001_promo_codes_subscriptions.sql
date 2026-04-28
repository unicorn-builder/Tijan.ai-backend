-- ============================================================
-- Migration 001 : Codes promo et abonnements
-- Projet : Tijan AI — Bureau d'etudes automatise
-- Date   : 2026-04-28
-- Auteur : Malick Tall (via Claude)
-- ============================================================

-- ============================================================
-- TABLE 1 : promo_codes
-- Stocke les codes promotionnels generes par l'admin
-- pour les prospects (cabinets d'etudes, entreprises BTP)
-- ============================================================

CREATE TABLE promo_codes (
  id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  code              text        UNIQUE NOT NULL,
  prospect_name     text        NOT NULL,
  prospect_email    text        NOT NULL,
  prospect_company  text,
  discount_percent  int         NOT NULL CHECK (discount_percent BETWEEN 1 AND 99),
  duration_months   int         NOT NULL CHECK (duration_months IN (3, 6)),
  expires_at        timestamptz NOT NULL,
  used_at           timestamptz,
  used_by_user_id   uuid        REFERENCES auth.users(id),
  created_by        uuid        REFERENCES auth.users(id),
  created_at        timestamptz DEFAULT now(),
  notes             text
);

-- ============================================================
-- TABLE 2 : subscriptions
-- Suivi des abonnements actifs avec periodes de reduction promo
-- ============================================================

CREATE TABLE subscriptions (
  id                    uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid        NOT NULL REFERENCES auth.users(id),
  plan                  text        NOT NULL DEFAULT 'cabinet_mensuel',
  status                text        NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active', 'cancelled', 'expired')),
  base_price_fcfa       int         NOT NULL DEFAULT 500000,
  current_price_fcfa    int         NOT NULL DEFAULT 500000,
  promo_code_id         uuid        REFERENCES promo_codes(id),
  discount_percent      int         DEFAULT 0,
  discount_start_at     timestamptz,
  discount_end_at       timestamptz,  -- calcule automatiquement : discount_start_at + duration_months
  credits_per_month     int         NOT NULL DEFAULT 3,
  current_period_start  timestamptz DEFAULT now(),
  current_period_end    timestamptz,
  created_at            timestamptz DEFAULT now(),
  updated_at            timestamptz DEFAULT now()
);

-- ============================================================
-- VUE : promo_codes_with_status
-- Ajoute un champ "statut" calcule dynamiquement
-- ============================================================

CREATE OR REPLACE VIEW promo_codes_with_status AS
SELECT *,
  CASE
    WHEN used_at IS NOT NULL THEN 'used'
    WHEN expires_at < now()  THEN 'expired'
    ELSE 'active'
  END AS statut
FROM promo_codes;

-- ============================================================
-- INDEX
-- ============================================================

-- Index sur l'email du prospect pour recherche rapide
CREATE INDEX idx_promo_codes_prospect_email ON promo_codes (prospect_email);

-- Index sur user_id pour les requetes d'abonnement par utilisateur
CREATE INDEX idx_subscriptions_user_id ON subscriptions (user_id);

-- Note : promo_codes(code) est deja indexe via la contrainte UNIQUE

-- ============================================================
-- RLS (Row Level Security)
-- ============================================================

-- Activer RLS sur les deux tables
ALTER TABLE promo_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- ----- promo_codes -----

-- Tous les utilisateurs authentifies peuvent lire (pour valider un code)
CREATE POLICY "promo_codes_select_authenticated"
  ON promo_codes
  FOR SELECT
  TO authenticated
  USING (true);

-- Seuls les admins peuvent inserer des codes promo
CREATE POLICY "promo_codes_insert_admin"
  ON promo_codes
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.jwt() ->> 'email' IN ('malicktall@gmail.com')
  );

-- Seuls les admins peuvent modifier (ou le backend via service role)
CREATE POLICY "promo_codes_update_admin"
  ON promo_codes
  FOR UPDATE
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN ('malicktall@gmail.com')
  )
  WITH CHECK (
    auth.jwt() ->> 'email' IN ('malicktall@gmail.com')
  );

-- Seuls les admins peuvent supprimer
CREATE POLICY "promo_codes_delete_admin"
  ON promo_codes
  FOR DELETE
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN ('malicktall@gmail.com')
  );

-- ----- subscriptions -----

-- Chaque utilisateur ne voit que ses propres abonnements
CREATE POLICY "subscriptions_select_own"
  ON subscriptions
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- INSERT et UPDATE via service role uniquement (backend)
-- Le role authenticated ne peut pas inserer directement
CREATE POLICY "subscriptions_insert_service"
  ON subscriptions
  FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "subscriptions_update_service"
  ON subscriptions
  FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

-- L'admin peut aussi voir tous les abonnements
CREATE POLICY "subscriptions_select_admin"
  ON subscriptions
  FOR SELECT
  TO authenticated
  USING (
    auth.jwt() ->> 'email' IN ('malicktall@gmail.com')
  );

-- ============================================================
-- GRANTS
-- Permissions explicites conformes aux regles Supabase RLS
-- ============================================================

GRANT ALL ON promo_codes TO authenticated;
GRANT ALL ON subscriptions TO authenticated;
GRANT ALL ON promo_codes_with_status TO authenticated;

-- ============================================================
-- Fin de la migration 001
-- ============================================================
