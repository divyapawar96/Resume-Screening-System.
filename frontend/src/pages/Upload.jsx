import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload as UploadIcon, FileText, X, ChevronRight, Briefcase, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const fadeInUp = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } }
};

const UploadPage = () => {
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [jobDescription, setJobDescription] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');
    const fileInputRef = useRef(null);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragging(true);
        } else if (e.type === 'dragleave') {
            setIsDragging(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const newFiles = Array.from(e.dataTransfer.files);
            setFiles(prev => [...prev, ...newFiles]);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const newFiles = Array.from(e.target.files);
            setFiles(prev => [...prev, ...newFiles]);
        }
    };

    const removeFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (files.length === 0 || !jobDescription.trim()) return;

        setUploading(true);
        setUploadStatus('Uploading resumes...');

        try {
            // 1. Upload Resumes
            const resumePromises = files.map(file => {
                const formData = new FormData();
                formData.append('file', file);
                return axios.post('http://127.0.0.1:8000/upload/resume', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
            });

            await Promise.all(resumePromises);

            // 2. Upload JD
            setUploadStatus('Analyzing job description...');
            const jdBlob = new Blob([jobDescription], { type: 'text/plain' });
            const jdFile = new File([jdBlob], "current_jd.txt", { type: "text/plain" });
            const jdFormData = new FormData();
            jdFormData.append('file', jdFile);

            const jdResponse = await axios.post('http://127.0.0.1:8000/upload/jd', jdFormData);
            const jdPath = jdResponse.data.saved_to;

            // 3. Rank
            setUploadStatus('Ranking candidates...');
            const rankResponse = await axios.post('http://127.0.0.1:8000/rank', {
                jd_path: jdPath,
                resumes_dir: "outputs/uploads", // Dependent on backend implementation
                top_n: 10
            });

            // Navigate to result
            navigate('/result', { state: { results: rankResponse.data } });

        } catch (error) {
            console.error("Analysis failed", error);
            alert("Analysis failed. Please check backend connection.");
        } finally {
            setUploading(false);
            setUploadStatus('');
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Simple Header */}
            <header className="navbar bg-white border-b border-slate-200">
                <div className="container py-4 flex-between">
                    <div className="font-bold text-xl text-primary flex items-center gap-2">
                        Resume<span className="text-accent">AI</span>
                    </div>
                </div>
            </header>

            <main className="container py-12">
                <motion.div
                    initial="hidden"
                    animate="visible"
                    className="grid-2 gap-8 items-start"
                >
                    {/* Left Column: Job Description */}
                    <motion.div variants={fadeInUp} className="space-y-6">
                        <div className="card h-full bg-white border-slate-200">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-blue-50 rounded-lg text-accent">
                                    <Briefcase size={24} />
                                </div>
                                <h2 className="text-xl font-semibold">Job Description</h2>
                            </div>
                            <p className="text-secondary text-sm mb-4">
                                Paste the job description below to match skills against candidates.
                            </p>
                            <textarea
                                className="w-full h-[400px] p-4 text-sm leading-relaxed border-slate-200 focus:ring-2 focus:ring-blue-100 resize-none rounded-xl bg-slate-50"
                                placeholder="Paste job description here (Role, Responsibilities, Required Skills...)"
                                value={jobDescription}
                                onChange={(e) => setJobDescription(e.target.value)}
                            />
                        </div>
                    </motion.div>

                    {/* Right Column: Upload */}
                    <motion.div variants={fadeInUp} transition={{ delay: 0.1 }} className="space-y-6">
                        <div className="card bg-white border-slate-200">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-blue-50 rounded-lg text-accent">
                                    <UploadIcon size={24} />
                                </div>
                                <h2 className="text-xl font-semibold">Upload Resumes</h2>
                            </div>

                            <div
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`
                                    border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all
                                    ${isDragging
                                        ? 'border-accent bg-blue-50'
                                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                                    }
                                `}
                            >
                                <input
                                    type="file"
                                    multiple
                                    className="hidden"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                    accept=".pdf,.docx,.txt"
                                />
                                <div className="flex flex-col items-center gap-4">
                                    <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center text-accent">
                                        <FileText size={24} />
                                    </div>
                                    <div>
                                        <p className="font-medium text-lg text-primary">Click or Drag files here</p>
                                        <p className="text-sm text-secondary mt-1">Supported formats: PDF, DOCX, TXT</p>
                                    </div>
                                </div>
                            </div>

                            {/* File List */}
                            <AnimatePresence>
                                {files.length > 0 && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="mt-6 space-y-3"
                                    >
                                        <div className="flex justify-between items-center text-sm text-secondary mb-2">
                                            <span>{files.length} files selected</span>
                                            <button
                                                onClick={() => setFiles([])}
                                                className="text-red-500 hover:text-red-600 text-xs font-medium"
                                            >
                                                Clear all
                                            </button>
                                        </div>
                                        <div className="max-h-[250px] overflow-y-auto pr-2 space-y-2 custom-scrollbar">
                                            {files.map((f, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    exit={{ opacity: 0, x: 10 }}
                                                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 group"
                                                >
                                                    <div className="flex items-center gap-3 overflow-hidden">
                                                        <FileText size={16} className="text-secondary shrink-0" />
                                                        <span className="text-sm truncate text-primary font-medium">{f.name}</span>
                                                    </div>
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                                                        className="text-slate-400 hover:text-red-500 transition-colors p-1"
                                                    >
                                                        <X size={16} />
                                                    </button>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <button
                                onClick={handleSubmit}
                                disabled={files.length === 0 || !jobDescription.trim() || uploading}
                                className={`
                                    w-full mt-6 btn btn-primary py-4 text-base flex justify-center items-center gap-2
                                    ${(files.length === 0 || !jobDescription.trim()) ? 'opacity-50 cursor-not-allowed' : ''}
                                `}
                            >
                                {uploading ? (
                                    <>
                                        <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                                        {uploadStatus}
                                    </>
                                ) : (
                                    <>
                                        Analyze Candidates <ChevronRight size={18} />
                                    </>
                                )}
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            </main>
        </div>
    );
};

export default UploadPage;
