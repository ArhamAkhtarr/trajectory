"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Award,
  BookOpen,
  Briefcase,
  Building2,
  CheckCircle2,
  Clock,
  Code,
  ExternalLink,
  FileText,
  Lightbulb,
  LogOut,
  MapPin,
  RefreshCw,
  Search,
  Sparkles,
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
  remote: boolean;
  url: string;
  source: string;
  posted_date: string;
  similarity_score?: number;
  fit_score?: number;
  reasoning?: string;
}

interface ProjectIdea {
  title: string;
  description: string;
  suggested_stack: string[];
  difficulty: string;
  estimated_hours: number;
}

interface ResumeAnalysis {
  file_reference_id: string;
  skills: string[];
  tools: string[];
  years_of_experience: number;
  suggested_roles: string[];
  text?: string;
  filename?: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; email?: string } | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Resume & Analysis State
  const [resumeData, setResumeData] = useState<ResumeAnalysis | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Matched Jobs Tab State
  const [searchQuery, setSearchQuery] = useState("python");
  const [matchedJobs, setMatchedJobs] = useState<MatchedJob[]>([]);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [matchedError, setMatchedError] = useState<string | null>(null);

  // Portfolio Ideas Tab State
  const [ideasLoading, setIdeasLoading] = useState(false);
  const [skillGaps, setSkillGaps] = useState<string[]>([]);
  const [projectIdeas, setProjectIdeas] = useState<ProjectIdea[]>([]);
  const [ideasError, setIdeasError] = useState<string | null>(null);

  // Auth Guard
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.push("/login");
      } else {
        setUser(session.user);
        setAuthLoading(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        router.push("/login");
      } else {
        setUser(session.user);
        setAuthLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  const handleSignOut = async () => {
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
        skills: analyzeResult.skills || [],
        tools: analyzeResult.tools || [],
        years_of_experience: analyzeResult.years_of_experience || 0,
        suggested_roles: analyzeResult.suggested_roles || [],
        text: uploadResult.text,
        filename: uploadResult.filename,
      };

      setResumeData(combined);
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
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Zap className="w-5 h-5 fill-current" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-indigo-600 to-indigo-500 bg-clip-text text-transparent">
              Trajectory Dashboard
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-xs text-slate-500 dark:text-slate-400 hidden sm:inline-flex items-center space-x-1.5">
              <UserCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>{user?.email}</span>
            </span>
            <Button
              onClick={handleSignOut}
              variant="outline"
              size="sm"
              className="rounded-lg text-xs font-semibold"
            >
              <LogOut className="w-3.5 h-3.5 mr-1.5" />
              <span>Sign Out</span>
            </Button>
          </div>
        </div>
      </header>

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

                          {job.reasoning && (
                            <p className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200/60 dark:border-slate-700/60 mt-3 italic">
                              &ldquo;{job.reasoning}&rdquo;
                            </p>
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
                      className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 rounded-2xl p-6 flex flex-col justify-between"
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
                        <div className="flex flex-wrap gap-1.5 pt-2">
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
                        <span className="text-indigo-600 dark:text-indigo-400 font-semibold cursor-pointer">
                          Start Project &rarr;
                        </span>
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
                {/* CV Overview Card */}
                <Card className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 rounded-2xl p-6">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4 mb-6">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                        <CheckCircle2 className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">
                          {resumeData.filename || "Uploaded Resume"}
                        </h3>
                        <p className="text-xs text-slate-500 font-mono">
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
                        Experience & Roles
                      </h4>
                      <p className="text-xs text-slate-700 dark:text-slate-300 font-semibold">
                        {resumeData.years_of_experience} Years Professional Experience
                      </p>
                      <div className="pt-1 space-y-1">
                        {resumeData.suggested_roles.map((role, i) => (
                          <div key={i} className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
                            &bull; {role}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Raw Extracted Text View */}
                {resumeData.text && (
                  <Card className="border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 rounded-2xl p-6">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
                      <BookOpen className="w-4 h-4" />
                      <span>Extracted Document Text</span>
                    </h4>
                    <pre className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800 text-xs font-mono text-slate-700 dark:text-slate-300 whitespace-pre-wrap max-h-80 overflow-y-auto">
                      {resumeData.text}
                    </pre>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
