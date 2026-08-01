"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, Mail, User, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { supabase } from "@/lib/supabaseClient";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    const savedEmail =
      typeof window !== "undefined"
        ? localStorage.getItem("trajectory_user_email")
        : null;
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session || savedEmail) {
        router.push("/dashboard");
      }
    });
  }, [router]);

  // Simple Account Access: Store user email & name in DB and enter dashboard directly (No code sending!)
  const handleAccountAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const emailClean = email.trim().toLowerCase();
      const nameClean = fullName.trim() || emailClean.split("@")[0];
      const userId = `user_${emailClean.replace(/[^a-zA-Z0-9]/g, "_")}`;

      // 1. Store user session in localStorage for immediate access
      if (typeof window !== "undefined") {
        localStorage.setItem("trajectory_user_email", emailClean);
        localStorage.setItem("trajectory_user_name", nameClean);
      }

      // 2. Persist user email & full name in Supabase profiles database table
      try {
        await fetch(`${API_BASE_URL}/user/profile/sync`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            email: emailClean,
            full_name: nameClean,
          }),
        });

        await supabase.from("profiles").upsert({
          id: userId,
          email: emailClean,
          full_name: nameClean,
          updated_at: new Date().toISOString(),
        });
      } catch (syncErr) {
        console.warn("Profile database sync notice:", syncErr);
      }

      // 3. Directly grant access and enter dashboard immediately (Zero codes sent!)
      router.push("/dashboard");
    } catch (err: unknown) {
      console.error("Account creation error:", err);
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      });

      if (error) throw error;
    } catch (err: unknown) {
      setMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Google OAuth sign in failed.",
      });
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center items-center px-6 py-12">
      <div className="w-full max-w-md">
        {/* Brand Logo */}
        <div className="flex items-center justify-center space-x-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
            <Zap className="w-6 h-6 fill-current" />
          </div>
          <span className="font-bold text-2xl tracking-tight text-slate-900 dark:text-slate-100">
            Trajectory
          </span>
        </div>

        <Card className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl rounded-2xl overflow-hidden">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-xl font-bold text-slate-900 dark:text-slate-100">
              Create Your Account
            </CardTitle>
            <CardDescription className="text-sm text-slate-500 dark:text-slate-400">
              Enter your name and email to save your profile and enter your dashboard instantly.
            </CardDescription>
          </CardHeader>

          <CardContent className="p-6 pt-4 space-y-6">
            {/* Google OAuth Button */}
            <Button
              type="button"
              variant="outline"
              onClick={handleGoogleLogin}
              disabled={loading}
              className="w-full py-5 rounded-xl border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 font-medium flex items-center justify-center space-x-3 text-slate-700 dark:text-slate-200"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </Button>

            <div className="relative flex items-center justify-center">
              <div className="border-t border-slate-200 dark:border-slate-800 w-full" />
              <span className="bg-white dark:bg-slate-900 px-3 text-xs text-slate-400 uppercase font-medium absolute">
                Or Sign Up with Email
              </span>
            </div>

            {/* Alert Message */}
            {message && (
              <div
                className={`p-4 rounded-xl text-sm leading-relaxed flex items-start space-x-2 ${
                  message.type === "success"
                    ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                    : "bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                ) : null}
                <span>{message.text}</span>
              </div>
            )}

            {/* DIRECT ACCOUNT CREATION FORM (NO EMAIL CODES) */}
            <form onSubmit={handleAccountAccess} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <Input
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="pl-10 rounded-xl"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="pl-10 rounded-xl"
                  />
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                  Your email and profile will be stored in our database. No confirmation code required.
                </p>
              </div>

              <Button
                type="submit"
                disabled={loading || !email.trim() || !fullName.trim()}
                className="w-full py-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <span>Creating Account & Entering Dashboard...</span>
                ) : (
                  <>
                    <span>Create Account & Enter Dashboard</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
