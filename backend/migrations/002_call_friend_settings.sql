-- =============================================================================
-- Migration: Call a Friend User Settings & Account Isolation
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.call_friend_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    caller_name TEXT NOT NULL DEFAULT 'Bro',
    language_code TEXT NOT NULL DEFAULT 'en-IN',
    voice_gender TEXT NOT NULL DEFAULT 'Male',
    speaker TEXT NOT NULL DEFAULT 'shubh',
    script TEXT NOT NULL DEFAULT 'Hey, where are you? I just wanted to check if you have reached safely.',
    duration_minutes INTEGER NOT NULL DEFAULT 2,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_call_friend_settings_user UNIQUE(user_id),
    CONSTRAINT chk_duration_minutes CHECK (duration_minutes IN (2, 5, 10)),
    CONSTRAINT chk_voice_gender CHECK (voice_gender IN ('Male', 'Female'))
);

-- Index for fast user lookup
CREATE INDEX IF NOT EXISTS idx_call_friend_settings_user_id ON public.call_friend_settings(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.call_friend_settings ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Users can view their own call friend settings" ON public.call_friend_settings;
DROP POLICY IF EXISTS "Users can insert their own call friend settings" ON public.call_friend_settings;
DROP POLICY IF EXISTS "Users can update their own call friend settings" ON public.call_friend_settings;
DROP POLICY IF EXISTS "Users can delete their own call friend settings" ON public.call_friend_settings;

-- RLS Policies
CREATE POLICY "Users can view their own call friend settings"
    ON public.call_friend_settings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own call friend settings"
    ON public.call_friend_settings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own call friend settings"
    ON public.call_friend_settings FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own call friend settings"
    ON public.call_friend_settings FOR DELETE
    USING (auth.uid() = user_id);

-- Automatic updated_at trigger function
CREATE OR REPLACE FUNCTION public.update_call_friend_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_call_friend_settings ON public.call_friend_settings;

CREATE TRIGGER trigger_update_call_friend_settings
    BEFORE UPDATE ON public.call_friend_settings
    FOR EACH ROW
    EXECUTE FUNCTION public.update_call_friend_settings_timestamp();