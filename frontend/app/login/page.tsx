"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, KeyRound, Mail, User, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { supabase } from "@/lib/supabaseClient";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [otpToken, setOtpToken] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.push("/dashboard");
      }
    });
  }, [router]);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: {
          data: { full_name: fullName.trim() || undefined },
          shouldCreateUser: true,
        },
      });

      if (error) throw error;

      setCodeSent(true);
      setMessage({
        type: "success",
        text: `A 6-digit confirmation code has been sent to ${email}. Please check your inbox or spam folder.`,
      });
    } catch (err: unknown) {
      setMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Could not send confirmation code. Please check your email address.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpToken.trim() || !email.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const { data, error } = await supabase.auth.verifyOtp({
        email: email.trim(),
        token: otpToken.trim(),
        type: "email",
      });

      if (error) throw error;

      if (data.session) {
        const user = data.session.user;
        // Sync profile to database
        try {
          await supabase.from("profiles").upsert({
            id: user.id,
            email: user.email,
            full_name: fullName.trim() || user.user_metadata?.full_name || email.split("@")[0],
            updated_at: new Date().toISOString(),
          });

          await fetch(`${API_BASE_URL}/user/profile/sync`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: user.id,
              email: user.email,
              full_name: fullName.trim() || user.user_metadata?.full_name || email.split("@")[0],
            }),
          });
        } catch (syncErr) {
          console.error("Profile sync warning:", syncErr);
        }

        router.push("/dashboard");
      }
    } catch (err: unknown) {
      setMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Invalid or expired confirmation code. Please try again.",
      });
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
              Sign In First to Access Trajectory
            </CardTitle>
            <CardDescription className="text-sm text-slate-500 dark:text-slate-400">
              Receive a secure confirmation code on your email to sign in or create an account.
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
                Or Email Confirmation Code
              </span>
            </div>

            {/* Success or Error Message Alert */}
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

            <Tabs defaultValue="sign-in" className="w-full">
              <TabsList className="grid w-full grid-cols-2 rounded-xl bg-slate-100 dark:bg-slate-800 p-1">
                <TabsTrigger
                  value="sign-in"
                  onClick={() => setCodeSent(false)}
                  className="rounded-lg text-xs font-semibold"
                >
                  Sign In
                </TabsTrigger>
                <TabsTrigger
                  value="sign-up"
                  onClick={() => setCodeSent(false)}
                  className="rounded-lg text-xs font-semibold"
                >
                  Create Account
                </TabsTrigger>
              </TabsList>

              {/* SIGN IN TAB */}
              <TabsContent value="sign-in" className="mt-4 space-y-4">
                {!codeSent ? (
                  <form onSubmit={handleSendOtp} className="space-y-4">
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
                    </div>

                    <Button
                      type="submit"
                      disabled={loading || !email.trim()}
                      className="w-full py-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium flex items-center justify-center space-x-2"
                    >
                      {loading ? (
                        <span>Sending Code...</span>
                      ) : (
                        <>
                          <span>Send Confirmation Code</span>
                          <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </Button>
                  </form>
                ) : (
                  <form onSubmit={handleVerifyOtp} className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        6-Digit Confirmation Code
                      </label>
                      <div className="relative">
                        <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                        <Input
                          type="text"
                          placeholder="123456"
                          value={otpToken}
                          onChange={(e) => setOtpToken(e.target.value)}
                          required
                          maxLength={6}
                          className="pl-10 tracking-widest text-center text-lg font-mono rounded-xl"
                        />
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                        Enter the code sent to <strong className="text-slate-800 dark:text-slate-200">{email}</strong>
                      </p>
                    </div>

                    <Button
                      type="submit"
                      disabled={loading || !otpToken.trim()}
                      className="w-full py-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
                    >
                      {loading ? <span>Verifying...</span> : <span>Verify & Sign In</span>}
                    </Button>

                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setCodeSent(false)}
                      className="w-full text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                    >
                      Use a different email address
                    </Button>
                  </form>
                )}
              </TabsContent>

              {/* CREATE ACCOUNT TAB */}
              <TabsContent value="sign-up" className="mt-4 space-y-4">
                {!codeSent ? (
                  <form onSubmit={handleSendOtp} className="space-y-4">
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
                    </div>

                    <Button
                      type="submit"
                      disabled={loading || !email.trim() || !fullName.trim()}
                      className="w-full py-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium flex items-center justify-center space-x-2"
                    >
                      {loading ? (
                        <span>Sending Confirmation Code...</span>
                      ) : (
                        <>
                          <span>Create Account & Send Code</span>
                          <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </Button>
                  </form>
                ) : (
                  <form onSubmit={handleVerifyOtp} className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        6-Digit Confirmation Code
                      </label>
                      <div className="relative">
                        <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                        <Input
                          type="text"
                          placeholder="123456"
                          value={otpToken}
                          onChange={(e) => setOtpToken(e.target.value)}
                          required
                          maxLength={6}
                          className="pl-10 tracking-widest text-center text-lg font-mono rounded-xl"
                        />
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                        Enter the code sent to <strong className="text-slate-800 dark:text-slate-200">{email}</strong>
                      </p>
                    </div>

                    <Button
                      type="submit"
                      disabled={loading || !otpToken.trim()}
                      className="w-full py-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
                    >
                      {loading ? <span>Completing Registration...</span> : <span>Verify & Complete Registration</span>}
                    </Button>

                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setCodeSent(false)}
                      className="w-full text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                    >
                      Change email or name
                    </Button>
                  </form>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
