import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { FileText, CheckCircle, BarChart2 } from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.2
        }
    }
};

const Home = () => {
    return (
        <div className="min-h-screen flex flex-col">
            {/* Navbar */}
            <nav className="navbar">
                <div className="container flex-between">
                    <Link to="/" className="text-xl font-bold text-primary flex items-center gap-2">
                        Resume<span className="text-accent">AI</span>
                    </Link>
                    <div>
                        <Link to="/upload" className="btn btn-primary text-sm">
                            Launch App
                        </Link>
                    </div>
                </div>
            </nav>

            <main className="flex-grow container">
                <motion.section
                    className="py-20 text-center max-w-4xl mx-auto"
                    initial="hidden"
                    animate="visible"
                    variants={staggerContainer}
                >
                    <motion.div variants={fadeInUp} className="mb-6 inline-block px-4 py-1.5 rounded-full bg-blue-50 text-accent text-sm font-medium border border-blue-100">
                        Professional HR Tool
                    </motion.div>
                    <motion.h1 className="text-4xl md:text-5xl font-bold mb-6 text-primary tracking-tight" variants={fadeInUp}>
                        AI-Based Resume Screening <br className="hidden md:block" /> & Skill Matching System
                    </motion.h1>
                    <motion.p className="text-lg text-secondary mb-10 leading-relaxed max-w-2xl mx-auto" variants={fadeInUp}>
                        Streamline your recruitment process with our enterprise-grade automated screening intelligence.
                        Instantly parse, match, and rank candidates against job descriptions with high precision.
                    </motion.p>
                    <motion.div variants={fadeInUp} className="flex justify-center gap-4">
                        <Link to="/upload" className="btn btn-primary text-lg px-8 py-3">
                            Start Screening
                        </Link>
                        <a href="#features" className="btn btn-secondary text-lg px-8 py-3">
                            Learn More
                        </a>
                    </motion.div>
                </motion.section>

                <motion.section
                    id="features"
                    className="grid-3 gap-8 mb-20"
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={staggerContainer}
                >
                    <FeatureCard
                        icon={<FileText size={28} />}
                        title="Smart Resume Parsing"
                        description="Automatically extract candidate details, skills, and experience from PDF and DOCX files with high accuracy."
                    />
                    <FeatureCard
                        icon={<CheckCircle size={28} />}
                        title="Semantic Matching"
                        description="Go beyond keywords. Our NLP engine understands context to match candidate capabilities with job requirements."
                    />
                    <FeatureCard
                        icon={<BarChart2 size={28} />}
                        title="Intelligent Ranking"
                        description="Get data-driven insights and ranked lists to identify top talent faster and reduce time-to-hire."
                    />
                </motion.section>
            </main>

            <footer className="py-8 border-t border-slate-200 mt-auto bg-white">
                <div className="container text-center text-secondary text-sm">
                    <p className="font-medium">Developed by Divya Arjun Pawar</p>
                    <p className="mt-2 text-xs text-muted">© 2026 AI Resume Screening System. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
};

const FeatureCard = ({ icon, title, description }) => (
    <motion.div className="card text-center hover:border-blue-200 transition-colors cursor-default" variants={fadeInUp}>
        <div className="text-accent mb-5 flex justify-center bg-blue-50 w-16 h-16 rounded-full items-center mx-auto">
            {icon}
        </div>
        <h3 className="text-lg font-semibold mb-3 text-primary">{title}</h3>
        <p className="text-secondary text-sm leading-relaxed">{description}</p>
    </motion.div>
);

export default Home;
