"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  Award,
  BookOpen,
  Briefcase,
  Building2,
  CheckCircle2,
  Clock,
  Code,
  ExternalLink,
  FileText,
  GraduationCap,
  Lightbulb,
  LogOut,
  MapPin,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  Upload,
  UserCheck,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { supabase } from "@/lib/supabaseClient";

interface MatchedJob {
  title: string;
  company: string;
  location: string;
  description?: string;
  remote: boolean;
  url: string;
  source: string;
  posted_date: string;
  similarity_score?: number;
  fit_score?: number;
  reasoning?: string;
}

interface ArchitecturePhase {
  phase: string;
  tasks: string[];
}

interface ProjectIdea {
  title: string;
  description: string;
  suggested_stack: string[];
  difficulty: string;
  estimated_hours: number;
  market_relevance?: string;
  architecture_pipeline?: ArchitecturePhase[];
  key_features?: string[];
  repository_structure?: string[];
}

interface ResumeAnalysis {
  file_reference_id: string;
  highest_education?: string;
  skills: string[];
  tools: string[];
  suggested_roles: string[];
  seniority_level?: string;
  summary_pitch?: string;
  key_strengths?: string[];
  top_recommendations?: string[];
  filename?: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; email?: string } | null>(null);
  const [isGuest, setIsGuest] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  // Selected Project Pipeline Modal State
  const [selectedProject, setSelectedProject] = useState<ProjectIdea | null>(null);

  // Resume & Analysis State
  const [resumeData, setResumeData] = useState<ResumeAnalysis | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Matched Jobs Tab State
  const [searchQuery, setSearchQuery] = useState("engineering");
  const [matchedJobs, setMatchedJobs] = useState<MatchedJob[]>([]);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [matchedError, setMatchedError] = useState<string | null>(null);

  // Portfolio Ideas Tab State
  const [ideasLoading, setIdeasLoading] = useState(false);
  const [skillGaps, setSkillGaps] = useState<string[]>([]);
  const [projectIdeas, setProjectIdeas] = useState<ProjectIdea[]>([]);
  const [ideasError, setIdeasError] = useState<string | null>(null);

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);

  // Auth Guard: Require Sign In First
  useEffect(() => {
    const savedEmail = typeof window !== "undefined" ? localStorage.getItem("trajectory_user_email") : null;

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser(session.user);
        setIsGuest(false);
      } else if (savedEmail) {
        setUser({ id: `user_${savedEmail.replace(/[^a-zA-Z0-9]/g, "_")}`, email: savedEmail });
        setIsGuest(false);
      } else {
        router.push("/login");
      }
      setAuthLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUser(session.user);
        setIsGuest(false);
      } else if (savedEmail) {
        setUser({ id: `user_${savedEmail.replace(/[^a-zA-Z0-9]/g, "_")}`, email: savedEmail });
        setIsGuest(false);
      } else {
        router.push("/login");
      }
      setAuthLoading(false);
    });

    return () => subscription.unsubscribe();
  }, [router]);

  const handleDeleteAccount = async () => {
    if (!user || user.id === "guest_user") return;
    setDeletingAccount(true);
    try {
      await fetch(`${API_BASE_URL}/user/account?user_id=${user.id}`, {
        method: "DELETE",
      });
      if (typeof window !== "undefined") {
        localStorage.removeItem("trajectory_user_email");
        localStorage.removeItem("trajectory_user_name");
      }
      await supabase.auth.signOut();
      router.push("/login");
    } catch (err) {
      console.error("Error deleting account:", err);
    } finally {
      setDeletingAccount(false);
      setShowDeleteModal(false);
    }
  };

  const handleSignOut = async () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("trajectory_user_email");
      localStorage.removeItem("trajectory_user_name");
    }
    await supabase.auth.signOut();
    router.push("/login");
  };

  // Upload Resume handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", user?.id || "default_user");

      // 1. Upload & Extract Resume Text
      const uploadRes = await fetch(`${API_BASE_URL}/resume/upload`, {
        method: "POST",
        body: formData,
      });

      if (!uploadRes.ok) {
        const errJson = await uploadRes.json();
        throw new Error(
          errJson.detail || `Upload failed with status ${uploadRes.status}`
        );
      }

      const uploadResult = await uploadRes.json();
      const refId = uploadResult.file_reference_id;

      // 2. Analyze Resume via LangGraph agent
      const analyzeRes = await fetch(`${API_BASE_URL}/resume/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_reference_id: refId,
          user_id: user?.id || "default_user",
        }),
      });

      if (!analyzeRes.ok) {
        throw new Error("Failed to analyze resume profile.");
      }

      const analyzeResult = await analyzeRes.json();

      const combined: ResumeAnalysis = {
        file_reference_id: refId,
        highest_education: analyzeResult.highest_education || "Bachelor's Degree",
        skills: analyzeResult.skills || [],
        tools: analyzeResult.tools || [],
        suggested_roles: analyzeResult.suggested_roles || [],
        seniority_level: analyzeResult.seniority_level || "Software Engineer",
        summary_pitch: analyzeResult.summary_pitch || "",
        key_strengths: analyzeResult.key_strengths || [],
        top_recommendations: analyzeResult.top_recommendations || [],
        filename: uploadResult.filename,
      };

      setResumeData(combined);

      if (analyzeResult.suggested_roles && analyzeResult.suggested_roles.length > 0) {
        setSearchQuery(analyzeResult.suggested_roles[0]);
      } else if (analyzeResult.skills && analyzeResult.skills.length > 0) {
        setSearchQuery(analyzeResult.skills[0]);
      }
    } catch (err: unknown) {
      console.error("Resume upload error:", err);
      setUploadError(
        err instanceof Error
          ? err.message
          : "Failed to process resume. Please make sure backend is running."
      );
    } finally {
      setUploading(false);
    }
  };

  // Fetch Matched Jobs
  const fetchMatchedJobs = async () => {
    if (!resumeData?.file_reference_id) return;

    setMatchingLoading(true);
    setMatchedError(null);

    try {
      const res = await fetch(
        `${API_BASE_URL}/jobs/matched?file_reference_id=${
          resumeData.file_reference_id
        }&query=${encodeURIComponent(searchQuery)}`
      );

      if (!res.ok) {
        throw new Error(`Matching failed (Status ${res.status})`);
      }

      const data = await res.json();
      setMatchedJobs(data.matched_jobs || []);
    } catch (err: unknown) {
      console.error("Matched jobs error:", err);
      setMatchedError(
        err instanceof Error
          ? err.message
          : "Failed to load vector matched & re-ranked jobs."
      );
    } finally {
      setMatchingLoading(false);
    }
  };

  // Fetch Portfolio Ideas
  const fetchPortfolioIdeas = async () => {
    if (!resumeData?.file_reference_id && (!resumeData?.skills || resumeData.skills.length === 0)) {
      return;
    }

    setIdeasLoading(true);
    setIdeasError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/ideas/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_reference_id: resumeData?.file_reference_id,
          skills: resumeData?.skills,
          target_roles: resumeData?.suggested_roles,
        }),
      });

      if (!res.ok) {
        throw new Error(`Idea generation failed (Status ${res.status})`);
      }

      const data = await res.json();
      setSkillGaps(data.skill_gaps || []);
      setProjectIdeas(data.project_ideas || []);
    } catch (err: unknown) {
      console.error("Ideas error:", err);
      setIdeasError(
        err instanceof Error
          ? err.message
          : "Failed to generate portfolio project ideas."
      );
    } finally {
      setIdeasLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center items-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-500">Checking authentication...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      {/* Header Banner */}
      <header className="border-b border-slate-200/80 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                <Zap className="w-5 h-5 fill-current" />
              </div>
              <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-indigo-600 to-indigo-500 bg-clip-text text-transparent">
                Trajectory Dashboard
              </span>
            </Link>

            <nav className="hidden md:flex items-center space-x-4 text-xs font-semibold text-slate-600 dark:text-slate-400">
              <Link
                href="/"
                className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
              >
                Job Search
              </Link>
              <Link
                href="/dashboard"
                className="text-indigo-600 dark:text-indigo-400 font-bold"
              >
                Resume Analyzer
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-xs text-slate-500 dark:text-slate-400 hidden sm:inline-flex items-center space-x-1.5">
              <UserCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>{user?.email}</span>
            </span>
            {isGuest ? (
              <Button
                onClick={() => router.push("/login")}
                variant="default"
                size="sm"
                className="rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <span>Sign In</span>
              </Button>
            ) : (
              <div className="flex items-center space-x-2">
                <Button
                  onClick={handleSignOut}
                  variant="outline"
                  size="sm"
                  className="rounded-lg text-xs font-semibold"
                >
                  <LogOut className="w-3.5 h-3.5 mr-1.5" />
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
              </div>
            )}
          </div>
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

      {/* Main Dashboard Container */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
        <Tabs defaultValue="my-cv" className="w-full space-y-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-4">
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                Career Command Center
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Analyze your CV, match vector-embedded roles, and generate skill-bridging projects.
              </p>
            </div>

            {/* Navigation Tabs */}
            <TabsList className="bg-slate-200/60 dark:bg-slate-800/60 p-1 rounded-xl">
              <TabsTrigger value="matched-jobs" className="rounded-lg text-xs font-semibold">
                <Briefcase className="w-3.5 h-3.5 mr-1.5" />
                <span>Matched Jobs</span>
              </TabsTrigger>
              <TabsTrigger value="portfolio-ideas" className="rounded-lg text-xs font-semibold">
                <Lightbulb className="w-3.5 h-3.5 mr-1.5" />
                <span>Portfolio Ideas</span>
              </TabsTrigger>
              <TabsTrigger value="my-cv" className="rounded-lg text-xs font-semibold">
                <FileText className="w-3.5 h-3.5 mr-1.5" />
                <span>My CV</span>
              </TabsTrigger>
            </TabsList>
          </div>

          {/* TAB 1: MATCHED JOBS */}
          <TabsContent value="matched-jobs" className="space-y-6">
            {!resumeData ? (
              <Card className="p-8 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl">
                <FileText className="w-12 h-12 text-slate-400 mx-auto mb-3 opacity-60" />
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200">
                  Please upload your CV first
                </h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto mt-1 mb-4">
                  Vector job matching computes cosine similarity between your CV embedding and open roles.
                </p>
                <Button
                  onClick={() => {
                    const tabElem = document.querySelector('[data-state="inactive"][value="my-cv"]') as HTMLElement;
                    tabElem?.click();
                  }}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold"
                >
                  Go to My CV Tab
                </Button>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Search Bar for Matched Jobs */}
                <Card className="p-6 border border-slate-200/80 dark:border-slate-800 rounded-2xl">
                  <div className="flex flex-col sm:flex-row gap-4 items-center">
                    <div className="relative flex-1 w-full">
                      <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" />
                      <Input
                        type="text"
                        placeholder="Search target job query (e.g. Python Developer, Full Stack)"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 h-11 rounded-xl"
                      />
                    </div>
                    <Button
                      onClick={fetchMatchedJobs}
                      disabled={matchingLoading}
                      className="w-full sm:w-auto h-11 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
                    >
                      {matchingLoading ? (
                        <span>Matching...</span>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Sparkles className="w-4 h-4" />
                          <span>Compute AI Match</span>
                        </div>
                      )}
                    </Button>
                  </div>
                </Card>

                {matchedError && (
                  <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 text-sm">
                    {matchedError}
                  </div>
                )}

                {/* Matched Job Results List */}
                <div className="space-y-4">
                  {matchedJobs.map((job, idx) => (
                    <Card
                      key={idx}
                      className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 hover:border-indigo-500/50 transition-all rounded-2xl p-6"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="space-y-1.5 flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                              {job.title}
                            </h3>
                            {job.fit_score && (
                              <Badge
                                className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                                  job.fit_score >= 85
                                    ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                                    : "bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30"
                                }`}
                              >
                                {job.fit_score}% AI Match
                              </Badge>
                            )}
                          </div>

                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-400">
                            <span className="flex items-center space-x-1">
                              <Building2 className="w-4 h-4 text-slate-400" />
                              <span>{job.company}</span>
                            </span>
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-4 h-4 text-slate-400" />
                              <span>{job.location}</span>
                            </span>
                          </div>

                          {/* Real Job Description Snippet from Source Site */}
                          {job.description && (
                            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pt-2 line-clamp-3">
                              {job.description}
                            </p>
                          )}

                          {job.reasoning && (
                            <div className="text-xs text-indigo-900 dark:text-indigo-200 bg-indigo-50/70 dark:bg-indigo-950/40 p-3 rounded-xl border border-indigo-200/60 dark:border-indigo-800/60 mt-3 font-medium flex items-start space-x-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
                              <span>{job.reasoning}</span>
                            </div>
                          )}
                        </div>

                        <Button
                          size="sm"
                          className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shrink-0"
                        >
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1.5"
                          >
                            <span>Apply</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* TAB 2: PORTFOLIO IDEAS */}
          <TabsContent value="portfolio-ideas" className="space-y-6">
            {!resumeData ? (
              <Card className="p-8 text-center border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl">
                <Lightbulb className="w-12 h-12 text-slate-400 mx-auto mb-3 opacity-60" />
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200">
                  Analyze your CV to unlock portfolio ideas
                </h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto mt-1 mb-4">
                  LangGraph agent identifies skill gaps and generates concrete project recommendations.
                </p>
              </Card>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
                      <Sparkles className="w-5 h-5 text-indigo-600" />
                      <span>AI Gap Analysis & Project Recommendations</span>
                    </h2>
                  </div>
                  <Button
                    onClick={fetchPortfolioIdeas}
                    disabled={ideasLoading}
                    className="rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs"
                  >
                    {ideasLoading ? (
                      <span>Generating Ideas...</span>
                    ) : (
                      <div className="flex items-center space-x-1.5">
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Generate Ideas</span>
                      </div>
                    )}
                  </Button>
                </div>

                {ideasError && (
                  <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 text-sm">
                    {ideasError}
                  </div>
                )}

                {/* Skill Gaps Header Card */}
                {skillGaps.length > 0 && (
                  <Card className="p-6 border border-amber-500/30 bg-amber-500/5 rounded-2xl">
                    <h3 className="text-xs font-extrabold uppercase tracking-wider text-amber-700 dark:text-amber-400 mb-3 flex items-center space-x-1.5">
                      <Award className="w-4 h-4" />
                      <span>Identified Skill Gaps to Bridge</span>
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {skillGaps.map((gap, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className="bg-white dark:bg-slate-900 border-amber-500/40 text-amber-800 dark:text-amber-300 text-xs font-semibold py-1 px-3"
                        >
                          {gap}
                        </Badge>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Project Ideas Cards Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {projectIdeas.map((idea, idx) => (
                    <Card
                      key={idx}
                      className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 rounded-2xl p-6 flex flex-col justify-between hover:border-indigo-500/50 transition-all shadow-sm"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-bold text-base text-slate-900 dark:text-slate-100">
                            {idea.title}
                          </h4>
                          <Badge variant="secondary" className="text-[10px] font-semibold shrink-0">
                            {idea.difficulty}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                          {idea.description}
                        </p>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {idea.suggested_stack.map((tech, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                            >
                              <Code className="w-2.5 h-2.5 mr-1" />
                              {tech}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="pt-4 mt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
                        <span className="flex items-center space-x-1">
                          <Clock className="w-3.5 h-3.5 text-indigo-500" />
                          <span>Est. {idea.estimated_hours} hours</span>
                        </span>
                        <Button
                          onClick={() => setSelectedProject(idea)}
                          variant="ghost"
                          size="sm"
                          className="text-indigo-600 dark:text-indigo-400 font-semibold hover:bg-indigo-50 dark:hover:bg-indigo-950/50 text-xs h-8 px-2"
                        >
                          Start Project &rarr;
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* TAB 3: MY CV */}
          <TabsContent value="my-cv" className="space-y-6">
            {!resumeData ? (
              <Card className="p-10 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl text-center bg-white dark:bg-slate-900/40">
                <div className="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mx-auto mb-4">
                  <Upload className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
                  Upload Your CV (PDF or DOCX)
                </h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mb-6">
                  Extract skills, tools, and experience level automatically via our LangGraph AI agent.
                </p>

                <div className="relative inline-block">
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc"
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    disabled={uploading}
                  />
                  <Button
                    disabled={uploading}
                    className="h-11 px-8 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-md shadow-indigo-500/20"
                  >
                    {uploading ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Extracting & Analyzing CV...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Upload className="w-4 h-4" />
                        <span>Select CV File</span>
                      </div>
                    )}
                  </Button>
                </div>

                {uploadError && (
                  <div className="mt-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 text-xs font-medium max-w-md mx-auto">
                    {uploadError}
                  </div>
                )}
              </Card>
            ) : (
              <div className="space-y-6">
                {/* CV Executive Overview Card */}
                <Card className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 rounded-2xl p-6 shadow-sm">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4 mb-6">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center font-bold text-lg">
                        <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100">
                            {resumeData.filename || "Uploaded Resume"}
                          </h3>
                          {resumeData.seniority_level && (
                            <Badge className="bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20 text-xs font-semibold">
                              {resumeData.seniority_level}
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 font-mono pt-0.5">
                          ID: {resumeData.file_reference_id}
                        </p>
                      </div>
                    </div>

                    <div className="relative">
                      <input
                        type="file"
                        accept=".pdf,.docx,.doc"
                        onChange={handleFileUpload}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        disabled={uploading}
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={uploading}
                        className="rounded-xl text-xs font-semibold"
                      >
                        <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                        <span>Re-upload Resume</span>
                      </Button>
                    </div>
                  </div>

                  {/* Executive Pitch Card */}
                  {resumeData.summary_pitch && (
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 mb-6">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center space-x-1">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                        <span>Executive Summary Pitch</span>
                      </h4>
                      <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                        {resumeData.summary_pitch}
                      </p>
                    </div>
                  )}

                  {/* Skills Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Extracted Skills
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {resumeData.skills.map((skill, i) => (
                          <Badge key={i} variant="secondary" className="text-xs font-medium">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Tools & Technologies
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {resumeData.tools.map((tool, i) => (
                          <Badge key={i} variant="outline" className="text-xs font-medium">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Highest Education & Target Roles
                      </h4>
                      {resumeData.highest_education && (
                        <div className="flex items-center space-x-1.5 text-xs text-indigo-600 dark:text-indigo-400 font-bold mb-2">
                          <GraduationCap className="w-4 h-4 shrink-0" />
                          <span>{resumeData.highest_education}</span>
                        </div>
                      )}
                      <div className="space-y-1">
                        {resumeData.suggested_roles.map((role, i) => (
                          <div key={i} className="text-xs text-slate-700 dark:text-slate-300 font-medium flex items-center space-x-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                            <span>{role}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Key Strengths & Recommendations Card */}
                {((resumeData.key_strengths && resumeData.key_strengths.length > 0) ||
                  (resumeData.top_recommendations && resumeData.top_recommendations.length > 0)) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {/* Strengths */}
                    <Card className="border border-emerald-500/30 bg-emerald-500/5 rounded-2xl p-6">
                      <h4 className="text-xs font-extrabold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-3 flex items-center space-x-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Core Profile Strengths</span>
                      </h4>
                      <ul className="space-y-2">
                        {resumeData.key_strengths?.map((str, i) => (
                          <li key={i} className="text-xs text-slate-700 dark:text-slate-300 flex items-start space-x-2">
                            <span className="text-emerald-500 font-bold">•</span>
                            <span>{str}</span>
                          </li>
                        ))}
                      </ul>
                    </Card>

                    {/* Recommendations */}
                    <Card className="border border-indigo-500/30 bg-indigo-500/5 rounded-2xl p-6">
                      <h4 className="text-xs font-extrabold uppercase tracking-wider text-indigo-700 dark:text-indigo-400 mb-3 flex items-center space-x-1.5">
                        <Sparkles className="w-4 h-4" />
                        <span>Resume Enhancement Insights</span>
                      </h4>
                      <ul className="space-y-2">
                        {resumeData.top_recommendations?.map((rec, i) => (
                          <li key={i} className="text-xs text-slate-700 dark:text-slate-300 flex items-start space-x-2">
                            <span className="text-indigo-500 font-bold">&rarr;</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Start Project Architecture Pipeline Modal */}
        {selectedProject && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <Card className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto space-y-6 animate-in fade-in zoom-in-95">
              <div className="flex items-start justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary" className="text-[10px] font-bold">
                      {selectedProject.difficulty}
                    </Badge>
                    <span className="text-xs text-slate-400 font-mono">
                      Est. {selectedProject.estimated_hours} Hours
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                    {selectedProject.title}
                  </h2>
                </div>
                <Button
                  onClick={() => setSelectedProject(null)}
                  variant="ghost"
                  size="sm"
                  className="rounded-full w-8 h-8 p-0 text-slate-400 hover:text-slate-600"
                >
                  ✕
                </Button>
              </div>

              {/* Market Relevance */}
              {selectedProject.market_relevance && (
                <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-700 dark:text-indigo-300 leading-relaxed font-medium">
                  <span className="font-bold block mb-1">🔥 Why This Project is High Demand in 2026:</span>
                  {selectedProject.market_relevance}
                </div>
              )}

              {/* Architecture Pipeline Phases */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-1.5">
                  <Code className="w-4 h-4 text-indigo-600" />
                  <span>Architecture & Implementation Pipeline</span>
                </h3>

                <div className="space-y-3">
                  {selectedProject.architecture_pipeline?.map((phaseObj, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 space-y-2"
                    >
                      <h4 className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
                        {phaseObj.phase}
                      </h4>
                      <ul className="space-y-1.5">
                        {phaseObj.tasks.map((task, j) => (
                          <li key={j} className="text-xs text-slate-700 dark:text-slate-300 flex items-center space-x-2">
                            <span className="w-3.5 h-3.5 rounded border border-slate-300 dark:border-slate-600 inline-block shrink-0" />
                            <span>{task}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Repo Structure */}
              {selectedProject.repository_structure && selectedProject.repository_structure.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Recommended Project Folder Structure
                  </h3>
                  <div className="p-4 rounded-xl bg-slate-950 text-slate-200 font-mono text-xs space-y-1">
                    {selectedProject.repository_structure.map((item, idx) => (
                      <div key={idx} className="text-slate-300">
                        📄 {item}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                <Button
                  onClick={() => setSelectedProject(null)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl px-6"
                >
                  Got It! Start Coding
                </Button>
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
