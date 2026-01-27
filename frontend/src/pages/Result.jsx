import React from 'react';
import { motion } from 'framer-motion';
import { useLocation, Link, Navigate } from 'react-router-dom';
import { Download, ChevronLeft, User, BarChart2, CheckCircle, XCircle } from 'lucide-react';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const ResultPage = () => {
    const location = useLocation();
    const result = location.state?.results; // Expecting { job: {...}, top_candidates: [...] }

    if (!result) {
        return <Navigate to="/upload" replace />;
    }

    const { job, top_candidates } = result;

    const exportPDF = () => {
        const doc = new jsPDF();
        doc.text(`Candidate Ranking Report: ${job.title || 'Job Analysis'}`, 14, 20);

        const tableColumn = ["Rank", "Name", "Match Score", "Matched Skills", "Missing Skills"];
        const tableRows = top_candidates.map((c, index) => [
            index + 1,
            c.name || c.file_path,
            `${(c.score || c.match_score || 0).toFixed(1)}%`,
            (c.matched_skills || c.skill_gap?.matched_skills || []).join(', '),
            (c.missing_skills || c.skill_gap?.missing_skills || []).join(', ')
        ]);

        doc.autoTable({
            startY: 30,
            head: [tableColumn],
            body: tableRows,
        });

        doc.save('candidate_ranking.pdf');
    };

    return (
        <div className="min-h-screen bg-slate-50 font-sans">
            <header className="navbar bg-white border-b border-slate-200 sticky top-0 z-10">
                <div className="container py-4 flex-between">
                    <div className="flex items-center gap-4">
                        <Link to="/upload" className="text-secondary hover:text-primary transition-colors">
                            <ChevronLeft size={24} />
                        </Link>
                        <h1 className="font-bold text-xl text-primary">Analysis Results</h1>
                    </div>
                    <button onClick={exportPDF} className="btn btn-secondary text-sm py-2 px-4 gap-2">
                        <Download size={16} /> Export Report
                    </button>
                </div>
            </header>

            <main className="container py-8">
                {/* Job Summary */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card mb-8 bg-white"
                >
                    <h2 className="text-lg font-semibold text-primary mb-2">Job Context: {job.title || "Uploaded Job Description"}</h2>
                    <div className="flex flex-wrap gap-2 mt-2">
                        {job.required_skills.slice(0, 10).map((skill, i) => (
                            <span key={i} className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-medium border border-slate-200">
                                {skill}
                            </span>
                        ))}
                        {job.required_skills.length > 10 && (
                            <span className="px-3 py-1 bg-slate-100 text-slate-400 rounded-full text-xs font-medium">
                                +{job.required_skills.length - 10} more
                            </span>
                        )}
                    </div>
                </motion.div>

                {/* Candidates List */}
                <div className="grid gap-6">
                    {top_candidates.map((candidate, index) => (
                        <CandidateCard key={index} candidate={candidate} rank={index + 1} />
                    ))}
                </div>
            </main>
        </div>
    );
};

const CandidateCard = ({ candidate, rank }) => {
    // Normalizing score to 0-100 if it's not already
    const score = candidate.skill_match_percentage || candidate.score || 0;
    const isHighMatch = score >= 70;
    const isMediumMatch = score >= 40 && score < 70;

    const statusColor = isHighMatch ? 'text-green-600 bg-green-50 border-green-200' :
        isMediumMatch ? 'text-yellow-600 bg-yellow-50 border-yellow-200' :
            'text-red-600 bg-red-50 border-red-200';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: rank * 0.1 }}
            className="card bg-white p-0 overflow-hidden border border-slate-200 hover:shadow-md transition-shadow"
        >
            <div className="p-6 grid md:grid-cols-[80px_2fr_1fr] gap-6 items-center">
                {/* Rank & Avatar */}
                <div className="flex flex-col items-center justify-center gap-2">
                    <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-bold text-lg">
                        #{rank}
                    </div>
                </div>

                {/* Details */}
                <div>
                    <h3 className="text-lg font-bold text-primary mb-1">{candidate.name || candidate.file_path}</h3>
                    <div className="flex items-center gap-4 text-sm text-secondary mb-3">
                        <span className="flex items-center gap-1"><User size={14} /> {candidate.email || 'No email provided'}</span>
                    </div>

                    {/* Skills */}
                    <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Matched:</span>
                            {(candidate.matched_skills || candidate.skill_gap?.matched_skills || []).slice(0, 5).map((s, i) => (
                                <span key={i} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-100">{s}</span>
                            ))}
                        </div>
                        {(candidate.missing_skills || candidate.skill_gap?.missing_skills || []).length > 0 && (
                            <div className="flex flex-wrap gap-2">
                                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Missing:</span>
                                {(candidate.missing_skills || candidate.skill_gap?.missing_skills || []).slice(0, 5).map((s, i) => (
                                    <span key={i} className="text-xs px-2 py-0.5 bg-red-50 text-red-700 rounded border border-red-100">{s}</span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Score */}
                <div className="text-center md:text-right border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 pl-0 md:pl-6">
                    <div className="text-sm text-secondary mb-1 font-medium">Match Score</div>
                    <div className={`text-3xl font-bold ${isHighMatch ? 'text-green-600' : isMediumMatch ? 'text-yellow-600' : 'text-slate-600'}`}>
                        {score.toFixed(0)}%
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
                        <div
                            className={`h-full rounded-full ${isHighMatch ? 'bg-green-500' : isMediumMatch ? 'bg-yellow-500' : 'bg-slate-400'}`}
                            style={{ width: `${Math.min(score, 100)}%` }}
                        />
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default ResultPage;
