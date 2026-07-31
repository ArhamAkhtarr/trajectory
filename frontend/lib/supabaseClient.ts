import { createClient } from "@supabase/supabase-js";

const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL ||
  "https://zwwurrpveswymieduvxb.supabase.co";

const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "sb_publishable_t4qmVs_eGRmeyB1nQ7LRXQ_RrpiJOrE";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
