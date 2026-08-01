-- ====================================================================
-- Trajectory Supabase Schema & Row-Level Security (RLS) Policies
-- ====================================================================

-- 1. Profiles Table (Stores user name, email, and CV summary)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    cv_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on profiles table
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Profiles RLS Policies
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can delete own profile"
    ON public.profiles FOR DELETE
    USING (auth.uid() = id);


-- 2. Resumes Table
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_reference_id TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    skills TEXT[],
    tools TEXT[],
    seniority_level TEXT,
    suggested_roles TEXT[],
    summary_pitch TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on resumes table
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

-- Resumes RLS Policies
CREATE POLICY "Users can view own resumes"
    ON public.resumes FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own resumes"
    ON public.resumes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own resumes"
    ON public.resumes FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own resumes"
    ON public.resumes FOR DELETE
    USING (auth.uid() = user_id);


-- 3. Profile Embeddings Table
CREATE TABLE IF NOT EXISTS public.profile_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    file_reference_id TEXT,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    highest_education TEXT,
    skills TEXT[],
    tools TEXT[],
    suggested_roles TEXT[],
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.profile_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile embeddings"
    ON public.profile_embeddings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile embeddings"
    ON public.profile_embeddings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile embeddings"
    ON public.profile_embeddings FOR DELETE
    USING (auth.uid() = user_id);


-- 4. Saved Searches Table
CREATE TABLE IF NOT EXISTS public.saved_searches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    country TEXT DEFAULT 'us',
    city TEXT,
    mode TEXT,
    is_freelance BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on saved_searches table
ALTER TABLE public.saved_searches ENABLE ROW LEVEL SECURITY;

-- Saved Searches RLS Policies
CREATE POLICY "Users can view own saved searches"
    ON public.saved_searches FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own saved searches"
    ON public.saved_searches FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own saved searches"
    ON public.saved_searches FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved searches"
    ON public.saved_searches FOR DELETE
    USING (auth.uid() = user_id);


-- 5. Supabase Storage RLS Policies for 'resumes' Bucket
CREATE POLICY "Users can view own resume storage files"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'resumes' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can upload own resume storage files"
    ON storage.objects FOR INSERT
    WITH CHECK (bucket_id = 'resumes' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can update own resume storage files"
    ON storage.objects FOR UPDATE
    USING (bucket_id = 'resumes' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can delete own resume storage files"
    ON storage.objects FOR DELETE
    USING (bucket_id = 'resumes' AND (storage.foldername(name))[1] = auth.uid()::text);
