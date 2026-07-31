-- ====================================================================
-- Trajectory Supabase Schema & Row-Level Security (RLS) Policies
-- ====================================================================

-- 1. Resumes Table
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_reference_id TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    skills TEXT[],
    tools TEXT[],
    years_of_experience NUMERIC(4, 1),
    suggested_roles TEXT[],
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on resumes table
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

-- Resumes RLS Policies: Users can only read, insert, update, and delete their own resume records
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


-- 2. Saved Searches Table
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

-- Saved Searches RLS Policies: Users can only read, insert, update, and delete their own search data
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


-- 3. Supabase Storage RLS Policies for 'resumes' Bucket
-- Users can only read, upload, and delete objects inside their own user_id directory
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
