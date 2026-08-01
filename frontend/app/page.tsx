"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  Briefcase,
  Building2,
  ExternalLink,
  Filter,
  Globe,
  LogOut,
  MapPin,
  Search,
  Sparkles,
  Trash2,
  UserCheck,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { COUNTRIES } from "@/lib/countries";
import { supabase } from "@/lib/supabaseClient";

interface Job {
  title: string;
  company: string;
  location: string;
  remote: boolean;
  url: string;
  source: string;
  posted_date: string;
}

interface ExternalLinkItem {
  platform: string;
  url: string;
  note: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SearchPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; email?: string } | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);

  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("us");
  const [city, setCity] = useState("");
  const [mode, setMode] = useState("all");
  const [isFreelance, setIsFreelance] = useState(false);

  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [externalLinks, setExternalLinks] = useState<ExternalLinkItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Require Sign In First: Redirect to /login if no active session
  useEffect(() => {
    const savedEmail = typeof window !== "undefined" ? localStorage.getItem("trajectory_user_email") : null;
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser(session.user);
      } else if (savedEmail) {
        setUser({ id: `user_${savedEmail.replace(/[^a-zA-Z0-9]/g, "_")}`, email: savedEmail });
      } else {
        router.push("/login");
      }
      setAuthLoading(false);
    });
  }, [router]);

  const handleSignOut = async () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("trajectory_user_email");
    }
    await supabase.auth.signOut();
    router.push("/login");
  };

  const handleDeleteAccount = async () => {
    if (!user) return;
    setDeletingAccount(true);
    try {
      await fetch(`${API_BASE_URL}/user/account?user_id=${user.id}`, {
        method: "DELETE",
      });
      if (typeof window !== "undefined") {
        localStorage.removeItem("trajectory_user_email");
      }
      await supabase.auth.signOut();
      router.push("/login");
    } catch (err) {
      console.error("Delete account error:", err);
    } finally {
      setDeletingAccount(false);
      setShowDeleteModal(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const searchParams = new URLSearchParams({
        query: query.trim(),
        country: country,
      });

      if (city.trim()) {
        searchParams.append("city", city.trim());
      }

      if (mode !== "all") {
        searchParams.append("mode", mode);
      }

      if (isFreelance) {
        // Adjust query context when in freelance mode if query doesn't specify
        if (!query.toLowerCase().includes("freelance")) {
          searchParams.set("query", `${query.trim()} freelance`);
        }
      }

      const res = await fetch(
        `${API_BASE_URL}/jobs/search?${searchParams.toString()}`
      );

      if (!res.ok) {
        throw new Error(`Failed to fetch jobs (Status: ${res.status})`);
      }

      const data = await res.json();
      setJobs(data.jobs || []);
      setExternalLinks(data.external_links || []);
    } catch (err: unknown) {
      console.error("Search error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Could not connect to search server. Make sure FastAPI backend is running on port 8000."
      );
      setJobs([]);
      setExternalLinks([]);
    } finally {
      setLoading(false);
    }
  };

  const getSourceBadgeColor = (source: string) => {
    switch (source.toLowerCase()) {
      case "adzuna":
        return "bg-emerald-500/10 text-emerald-600 border-emerald-500/20 dark:text-emerald-400";
      case "remotive":
        return "bg-indigo-500/10 text-indigo-600 border-indigo-500/20 dark:text-indigo-400";
      case "remoteok":
        return "bg-rose-500/10 text-rose-600 border-rose-500/20 dark:text-rose-400";
      case "arbeitnow":
        return "bg-amber-500/10 text-amber-600 border-amber-500/20 dark:text-amber-400";
      case "jooble":
        return "bg-cyan-500/10 text-cyan-600 border-cyan-500/20 dark:text-cyan-400";
      default:
        return "bg-slate-500/10 text-slate-600 border-slate-500/20 dark:text-slate-400";
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center items-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-500">Redirecting to Sign In...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      {/* Header Banner */}
      <header className="border-b border-slate-200/80 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Zap className="w-5 h-5 fill-current" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-indigo-600 to-indigo-500 bg-clip-text text-transparent">
              Trajectory
            </span>
          </div>
          <nav className="flex items-center space-x-6 text-sm font-medium text-slate-600 dark:text-slate-400">
            <Link
              href="/"
              className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
            >
              Job Search
            </Link>
            <Link
              href="/dashboard"
              className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors hover:underline"
            >
              Resume Analyzer
            </Link>

            <span className="text-xs text-slate-500 dark:text-slate-400 hidden sm:inline-flex items-center space-x-1">
              <UserCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>{user?.email}</span>
            </span>

            <Button
              onClick={handleSignOut}
              variant="outline"
              size="sm"
              className="rounded-lg text-xs font-semibold"
            >
              <LogOut className="w-3.5 h-3.5 mr-1" />
              <span>Sign Out</span>
            </Button>

            <Button
              onClick={() => setShowDeleteModal(true)}
              variant="ghost"
              size="sm"
              className="rounded-lg text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40"
            >
              <Trash2 className="w-3.5 h-3.5 mr-1" />
              <span>Delete Account</span>
            </Button>
          </nav>
        </div>
      </header>

      {/* Delete Account Modal Confirmation */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
          <Card className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl rounded-2xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <AlertTriangle className="w-6 h-6 shrink-0" />
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Delete Account Permanently?
              </h3>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              This will permanently delete your user profile (<strong className="text-slate-800 dark:text-slate-200">{user?.email}</strong>), stored resume files, search history, and analysis records. This action cannot be undone.
            </p>
            <div className="flex items-center justify-end space-x-3 pt-2">
              <Button
                variant="outline"
                onClick={() => setShowDeleteModal(false)}
                disabled={deletingAccount}
                className="rounded-xl text-xs"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteAccount}
                disabled={deletingAccount}
                className="rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white"
              >
                {deletingAccount ? "Deleting Account..." : "Yes, Delete My Account"}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-12 flex flex-col items-center">
        {/* Title Hero */}
        <div className="text-center max-w-2xl mb-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/60 dark:border-indigo-800/60 text-xs font-semibold text-indigo-700 dark:text-indigo-300 mb-4 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Multi-Source AI Job Aggregator</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 mb-3">
            Find Your Next Career Move
          </h1>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 leading-relaxed">
            Search across Adzuna, Remotive, RemoteOK, Arbeitnow, and Jooble simultaneously.
          </p>
        </div>

        {/* Search Card Form */}
        <Card className="w-full shadow-xl shadow-slate-200/50 dark:shadow-none border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/90 rounded-2xl overflow-hidden mb-12">
          <CardContent className="p-6 sm:p-8">
            <form onSubmit={handleSearch} className="space-y-6">
              {/* Primary Query Bar */}
              <div className="relative">
                <Search className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
                <Input
                  type="text"
                  placeholder="Job title, keywords, or skills (e.g. Python Developer, React, DevOps)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-12 h-12 text-base rounded-xl border-slate-200 dark:border-slate-800 focus-visible:ring-indigo-500 shadow-sm"
                  required
                />
              </div>

              {/* Filters Grid */}
              <div
                className={`grid grid-cols-1 ${
                  isFreelance ? "sm:grid-cols-2" : "sm:grid-cols-3"
                } gap-4`}
              >
                {/* Country Dropdown (Hidden in Freelance / Gig Mode) */}
                {!isFreelance && (
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center space-x-1">
                      <Globe className="w-3.5 h-3.5" />
                      <span>Country</span>
                    </label>
                    <Select
                      value={country}
                      onValueChange={(val) => setCountry(val || "us")}
                    >
                      <SelectTrigger className="h-11 rounded-xl border-slate-200 dark:border-slate-800">
                        <SelectValue placeholder="Select Country" />
                      </SelectTrigger>
                      <SelectContent>
                        {COUNTRIES.map((c) => (
                          <SelectItem key={c.code} value={c.code}>
                            <span className="mr-2">{c.flag}</span>
                            {c.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* City Input */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>City (Optional)</span>
                  </label>
                  <Input
                    type="text"
                    placeholder="e.g. San Francisco"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="h-11 rounded-xl border-slate-200 dark:border-slate-800"
                  />
                </div>

                {/* Mode Select */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center space-x-1">
                    <Filter className="w-3.5 h-3.5" />
                    <span>Work Mode</span>
                  </label>
                  <Select value={mode} onValueChange={(val) => setMode(val || "all")}>
                    <SelectTrigger className="h-11 rounded-xl border-slate-200 dark:border-slate-800">
                      <SelectValue placeholder="All Modes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Any Mode</SelectItem>
                      <SelectItem value="remote">🌐 Remote Only</SelectItem>
                      <SelectItem value="onsite">🏢 On-site</SelectItem>
                      <SelectItem value="hybrid">⚡ Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Toggle & Submit Action */}
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4">
                {/* Job vs Freelance Toggle */}
                <div className="flex items-center space-x-3">
                  <Switch
                    id="freelance-mode"
                    checked={isFreelance}
                    onCheckedChange={setIsFreelance}
                  />
                  <label
                    htmlFor="freelance-mode"
                    className="text-sm font-medium cursor-pointer text-slate-700 dark:text-slate-300 select-none flex items-center space-x-2"
                  >
                    <span>
                      {isFreelance ? "Freelance / Gig Mode" : "Full-Time Jobs"}
                    </span>
                    {isFreelance && (
                      <Badge variant="secondary" className="text-[10px] py-0">
                        Gig Search
                      </Badge>
                    )}
                  </label>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="w-full sm:w-auto h-11 px-8 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-md shadow-indigo-500/20 transition-all"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Searching...</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Search className="w-4 h-4" />
                      <span>Search Opportunities</span>
                    </div>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Error Alert */}
        {error && (
          <div className="w-full p-4 mb-8 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-sm font-medium text-center">
            {error}
          </div>
        )}

        {/* Results Container */}
        {hasSearched && (
          <div className="w-full space-y-10">
            {/* Header Result Count */}
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center space-x-2">
                <Briefcase className="w-5 h-5 text-indigo-600" />
                <span>Job Listings</span>
                <Badge variant="outline" className="ml-2 font-mono text-xs">
                  {jobs.length} results
                </Badge>
              </h2>
            </div>

            {/* Loading Skeletons */}
            {loading && (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="w-full h-32 rounded-2xl bg-slate-200/60 dark:bg-slate-800/50 animate-pulse border border-slate-200/50 dark:border-slate-800"
                  />
                ))}
              </div>
            )}

            {/* Empty State */}
            {!loading && jobs.length === 0 && (
              <div className="text-center py-16 bg-white dark:bg-slate-900/50 rounded-2xl border border-slate-200/80 dark:border-slate-800">
                <Building2 className="w-12 h-12 mx-auto text-slate-400 mb-3 opacity-60" />
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
                  No jobs found matching your criteria
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
                  Try broadening your search term or selecting a different country/work mode.
                </p>
              </div>
            )}

            {/* Job Cards Grid */}
            {!loading && jobs.length > 0 && (
              <div className="space-y-4">
                {jobs.map((job, idx) => (
                  <Card
                    key={idx}
                    className="group border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 hover:border-indigo-500/50 dark:hover:border-indigo-500/50 transition-all duration-200 rounded-2xl shadow-sm hover:shadow-md"
                  >
                    <CardHeader className="p-6 pb-4">
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="space-y-1">
                          <CardTitle className="text-lg font-bold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {job.title}
                          </CardTitle>
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-600 dark:text-slate-400 pt-1">
                            <span className="flex items-center space-x-1.5 font-medium">
                              <Building2 className="w-4 h-4 text-slate-400" />
                              <span>{job.company || "Company Undisclosed"}</span>
                            </span>
                            <span className="flex items-center space-x-1.5">
                              <MapPin className="w-4 h-4 text-slate-400" />
                              <span>{job.location || "Location Flexible"}</span>
                            </span>
                          </div>
                        </div>

                        {/* Source Badge & Work Mode */}
                        <div className="flex items-center space-x-2 shrink-0">
                          {job.remote && (
                            <Badge
                              variant="secondary"
                              className="bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 text-xs font-semibold"
                            >
                              Remote
                            </Badge>
                          )}
                          <Badge
                            variant="outline"
                            className={`text-xs font-semibold capitalize border ${getSourceBadgeColor(
                              job.source
                            )}`}
                          >
                            {job.source}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>

                    <CardContent className="px-6 pb-6 pt-0 flex items-center justify-between border-t border-slate-100 dark:border-slate-800/50 mt-4">
                      <span className="text-xs text-slate-400 pt-4">
                        {job.posted_date
                          ? `Posted: ${new Date(job.posted_date).toLocaleDateString()}`
                          : "Recently posted"}
                      </span>
                      <Button
                        variant="default"
                        size="sm"
                        className="mt-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium shadow-sm transition-all"
                      >
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5"
                        >
                          <span>Apply Now</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Search More Platforms Section */}
            {externalLinks.length > 0 && (
              <div className="pt-10 border-t border-slate-200/80 dark:border-slate-800 mt-12">
                <div className="mb-6">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    Search More Platforms
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Direct pre-filled search links to external job portals & gig platforms.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {externalLinks.map((link, idx) => (
                    <Card
                      key={idx}
                      className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/60 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors rounded-xl p-5 flex items-center justify-between"
                    >
                      <div className="space-y-0.5">
                        <h4 className="font-semibold text-slate-900 dark:text-slate-100 text-base">
                          {link.platform}
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {link.note}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="rounded-lg border-slate-300 dark:border-slate-700"
                      >
                        <a
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 text-xs font-semibold"
                        >
                          <span>Open</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </Button>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-slate-200/80 dark:border-slate-800 py-8 text-center text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-5xl mx-auto px-6">
          Trajectory Monorepo &copy; 2026. Built with Next.js 14, Tailwind CSS, & FastAPI.
        </div>
      </footer>
    </div>
  );
}
