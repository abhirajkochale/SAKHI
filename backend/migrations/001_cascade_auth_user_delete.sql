-- =============================================================================
-- Migration: Automatic Cleanup & Account Isolation on Auth User Deletion
-- =============================================================================
-- This script ensures that when a user account is deleted from Supabase Auth
-- (auth.users), the corresponding public.users record is automatically deleted
-- via PostgreSQL foreign key ON DELETE CASCADE or Trigger, preventing orphaned
-- user rows and ensuring that re-registered Google accounts start clean as NORMAL.

-- Option A: Foreign Key ON DELETE CASCADE (Recommended for PostgreSQL)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_public_users_auth_users'
    ) THEN
        ALTER TABLE public.users
        ADD CONSTRAINT fk_public_users_auth_users
        FOREIGN KEY (id)
        REFERENCES auth.users (id)
        ON DELETE CASCADE;
    END IF;
END $$;

-- Option B: PostgreSQL Trigger for auth.users cleanup (Alternative)
CREATE OR REPLACE FUNCTION public.handle_auth_user_deleted()
RETURNS TRIGGER AS $$
BEGIN
  DELETE FROM public.users WHERE id = OLD.id;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists to allow idempotency
DROP TRIGGER IF EXISTS on_auth_user_deleted ON auth.users;

CREATE TRIGGER on_auth_user_deleted
  AFTER DELETE ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_auth_user_deleted();