import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import benchmarkDataImport from './data/benchmarkData.json';

// EmailOctopus Form Components
interface EmailFormProps {
  listType: 'waitlist' | 'newsletter';
  placeholder: string;
}

const EmailOctopusForm: React.FC<EmailFormProps> = ({ listType, placeholder }) => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setStatus('loading');

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          listType
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(data.message);
        setEmail('');
      } else {
        setStatus('error');
        if (data.code === 'ALREADY_SUBSCRIBED') {
          setMessage('This email is already subscribed!');
        } else {
          setMessage(data.error || 'Something went wrong. Please try again.');
        }
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error. Please try again.');
    }
  };

  return (
    <div className="emailoctopus-form-wrapper">
      <form onSubmit={handleSubmit} className="email-form-inline">
        <div className="email-input-group">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={placeholder}
            required
            disabled={status === 'loading'}
            className="email-input"
          />
          <button
            type="submit"
            disabled={status === 'loading' || !email}
            className="email-submit-btn cool-btn"
          >
            {status === 'loading' ? (
              <span className="loading-spinner">⚡</span>
            ) : (
              <>
                <span className="btn-text">Sign Up</span>
                <span className="btn-arrow">→</span>
              </>
            )}
          </button>
        </div>
      </form>

      {status === 'success' && (
        <div className="emailoctopus-form-success">{message}</div>
      )}

      {status === 'error' && (
        <div className="emailoctopus-form-error">{message}</div>
      )}
    </div>
  );
};

interface BenchmarkRow {
  subject: string;
  skill: string;
  topic?: string;
  grade: number;
  count: number;
  p50?: string;
  p90: string;
  p95: string;
  p99: string;
  avgTime?: string;
  eduBenchEC?: string;
  eduBenchIP?: string;
  eduBenchQA?: string;
  eduBenchOverall?: string;
  arabicSimilarity?: string;
  scaffoldingQuality?: string;
  mathAccuracy?: string;
  culturalRelevance?: string;
  imageQuality?: string;
  multiModal?: string;
  errorRate?: string;
  cost?: string;
}

interface ApproachConfig {
  id: string;
  name: string;
  description: string;
  color: string;
  features: string[];
  data: BenchmarkRow[];
}

function App() {
  // Performance data managed through comprehensive provider/grade tables
  const [openFAQs, setOpenFAQs] = useState<Record<string, boolean>>({});
  const [selectedSignupType, setSelectedSignupType] = useState<'waitlist' | 'newsletter'>('waitlist');
  const [openApproaches, setOpenApproaches] = useState<Record<string, boolean>>({
    'gpt4-arabic': false,
    'falcon-arabic': false,
    'dspy-falcon': true,
    'openai-falcon': false
  });
  const [searchTerms, setSearchTerms] = useState<Record<string, string>>({
    'gpt4-arabic': '',
    'falcon-arabic': '',
    'dspy-falcon': '',
    'openai-falcon': ''
  });

  const approaches: ApproachConfig[] = benchmarkDataImport.approaches as ApproachConfig[];

  const toggleFAQ = (id: string) => {
    setOpenFAQs(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const toggleApproach = (id: string) => {
    setOpenApproaches(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const updateSearchTerm = (id: string, term: string) => {
    setSearchTerms(prev => ({
      ...prev,
      [id]: term
    }));
  };

  const getFilteredData = (approachId: string, data: BenchmarkRow[]) => {
    const searchTerm = searchTerms[approachId]?.toLowerCase() || '';
    if (!searchTerm) return data;

    return data.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(searchTerm)
      )
    );
  };

  return (
    <div className="app">
      {/* Hero Section */}
      <section className="hero">
        {/* Luxury decorative elements */}
        <div className="luxury-bg-elements">
          {/* Floating geometric shapes */}
          <motion.div
            className="floating-shape shape-1"
            animate={{
              y: [-20, -40, -20],
              rotate: [0, 360],
              scale: [1, 1.1, 1]
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
              <path d="M30 5L50 25L30 45L10 25L30 5Z" stroke="url(#gradient1)" strokeWidth="1" fill="rgba(0, 212, 170, 0.05)" />
              <defs>
                <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00D4AA" />
                  <stop offset="100%" stopColor="#00B894" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>

          <motion.div
            className="floating-shape shape-2"
            animate={{
              y: [0, -30, 0],
              rotate: [0, -360],
              scale: [1, 0.9, 1]
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 2
            }}
          >
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" stroke="url(#gradient2)" strokeWidth="1" fill="rgba(0, 212, 170, 0.02)" />
              <circle cx="20" cy="20" r="10" stroke="url(#gradient2)" strokeWidth="0.5" fill="rgba(0, 212, 170, 0.03)" />
              <defs>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00D4AA" />
                  <stop offset="100%" stopColor="#E5E5E5" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>

          <motion.div
            className="floating-shape shape-3"
            animate={{
              y: [-10, -50, -10],
              rotate: [0, 180, 360],
              x: [0, 20, 0]
            }}
            transition={{
              duration: 12,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 4
            }}
          >
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <path d="M40 10L60 30L40 50L20 30L40 10Z" stroke="url(#gradient3)" strokeWidth="0.8" fill="none" />
              <path d="M40 20L50 30L40 40L30 30L40 20Z" stroke="url(#gradient3)" strokeWidth="0.5" fill="rgba(0, 228, 186, 0.02)" />
              <defs>
                <linearGradient id="gradient3" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00E4BA" />
                  <stop offset="50%" stopColor="#FFE55C" />
                  <stop offset="100%" stopColor="#00E4BA" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>

          {/* Flowing lines */}
          <motion.div
            className="flowing-line line-1"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <svg width="200" height="100" viewBox="0 0 200 100" fill="none">
              <motion.path
                d="M0 50 Q50 10 100 50 T200 50"
                stroke="url(#lineGradient1)"
                strokeWidth="1"
                fill="none"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              />
              <defs>
                <linearGradient id="lineGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="transparent" />
                  <stop offset="50%" stopColor="#00E4BA" />
                  <stop offset="100%" stopColor="transparent" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>
        </div>

        <div className="hero-content">
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="hero-title"
          >
            <span className="title-gradient">Agentic Educational</span>
            <span className="title-line">Question Generation</span>
          </motion.h1>


          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="feature-tags"
          >
            {['DSPy-Controlled Agents', '100 Questions/20min', 'Multi-Modal Output', 'Arabic & English', 'Autonomous Reasoning', 'Parallel Execution'].map((feature) => (
              <div key={feature} className="feature-tag">
                {feature}
              </div>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="cta-buttons"
          >
 
            <a href="#benchmark-section" className="btn btn-secondary">

            <svg className="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
              Benchmarks
            </a>
            <a href="#faq-section" className="btn btn-api"> 
              <svg className="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              See FAQ
            </a>
          </motion.div>
        </div>
      </section>

      {/* Benchmarks */}
      <section className="benchmark-section" id="benchmark-section">
        {/* Left side decorative elements */}
        <div className="luxury-left-elements">
          <motion.div
            className="side-ornament"
            animate={{
              y: [0, -20, 0],
              opacity: [0.3, 0.7, 0.3]
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <svg width="120" height="200" viewBox="0 0 120 200" fill="none">
              <path d="M20 20 Q60 40 100 20 Q80 100 100 180 Q60 160 20 180 Q40 100 20 20"
                    stroke="url(#sideGradient1)" strokeWidth="0.5" fill="rgba(0, 228, 186, 0.02)" />
              <defs>
                <linearGradient id="sideGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00E4BA" />
                  <stop offset="50%" stopColor="#FFE55C" />
                  <stop offset="100%" stopColor="#00E4BA" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>
        </div>

        {/* Right side decorative elements */}
        <div className="luxury-right-elements">
          <motion.div
            className="side-ornament"
            animate={{
              rotate: [0, 180, 360],
              scale: [1, 1.2, 1]
            }}
            transition={{
              duration: 15,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
              <polygon points="50,15 85,35 85,65 50,85 15,65 15,35"
                       stroke="url(#sideGradient2)" strokeWidth="0.8" fill="none" />
              <polygon points="50,25 75,35 75,65 50,75 25,65 25,35"
                       stroke="url(#sideGradient2)" strokeWidth="0.4" fill="rgba(255, 229, 92, 0.03)" />
              <defs>
                <linearGradient id="sideGradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FFE55C" />
                  <stop offset="100%" stopColor="#00E4BA" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>

          <motion.div
            className="floating-dots"
            animate={{
              y: [-10, 10, -10],
              x: [-5, 5, -5]
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 1
            }}
          >
            <svg width="60" height="120" viewBox="0 0 60 120" fill="none">
              <circle cx="30" cy="20" r="2" fill="#00E4BA" opacity="0.6" />
              <circle cx="30" cy="40" r="1.5" fill="#FFE55C" opacity="0.4" />
              <circle cx="30" cy="60" r="2.5" fill="#00E4BA" opacity="0.5" />
              <circle cx="30" cy="80" r="1" fill="#FFE55C" opacity="0.7" />
              <circle cx="30" cy="100" r="2" fill="#00E4BA" opacity="0.3" />
            </svg>
          </motion.div>
        </div>

        <div className="section-content">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="section-title">
              <span className="title-gradient">Performance Benchmarks</span>
            </h2>
          </motion.div>


                    {/* Quality Metrics */}
          <div className="benchmark-stats" style={{ margin: '3rem 0 1rem' }}>
            <div className="stat-item">
              <div className="stat-label">EduBench (External)</div>
              <div className="stat-value">82.7%</div>
              <div className="stat-subtitle">EC, IP, QA task types</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Arabic Similarity (Internal)</div>
              <div className="stat-value">95.6%</div>
              <div className="stat-subtitle">Translation quality</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Scaffolding Quality (Internal)</div>
              <div className="stat-value">96.6%</div>
              <div className="stat-subtitle">Instruction structure</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Math Accuracy (Internal)</div>
              <div className="stat-value">XX.X%</div>
              <div className="stat-subtitle">Content validation</div>
            </div>
          </div>

          {/* Benchmark Explanation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="benchmark-explanation"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(0, 212, 170, 0.2)',
              borderRadius: '12px',
              padding: '1.5rem',
              marginBottom: '2rem'
            }}
          >
            <h3 style={{ color: '#00D4AA', marginBottom: '1rem', fontSize: '1.2rem' }}>Our Benchmarking Approach</h3>
            <div style={{ display: 'grid', gap: '1rem', color: '#E0E0E0', fontSize: '0.95rem' }}>
              <div>
                <strong style={{ color: '#FFE55C' }}>External Benchmarks:</strong>
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                  <li><strong>EduBench (EDU-Qwen2.5-7B)</strong> - Industry-standard benchmark measuring question quality across three task types:
                    <ul style={{ paddingLeft: '1.5rem', marginTop: '0.25rem' }}>
                      <li><strong>EC (External Constraints)</strong> - Adherence to curriculum standards</li>
                      <li><strong>IP (Item Prompt)</strong> - Question clarity and appropriateness</li>
                      <li><strong>QA (Question Authoring)</strong> - Overall authoring quality</li>
                    </ul>
                    <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#B0B0B0' }}>
                      Hosted via HuggingFace (DirectionAI/EDU-Qwen2.5-7B) on 1x Nvidia A100 80GB GPU
                    </div>
                  </li>
                </ul>
              </div>
              <div>
                <strong style={{ color: '#FFE55C' }}>Internal Metrics:</strong>
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                  <li><strong>Arabic Similarity</strong> - Measures how closely generated Arabic questions match native Arabic educational content, ensuring cultural and linguistic authenticity</li>
                  <li><strong>Scaffolding Quality</strong> - Evaluates the structure and pedagogical effectiveness of step-by-step explanations and instructional support</li>
                  <li><strong>Math Accuracy</strong> - Validates mathematical correctness of problems, solutions, and calculations</li>
                </ul>
              </div>
            </div>
          </motion.div>

          {/* Infrastructure Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            viewport={{ once: true }}
            className="infrastructure-details"
            style={{
              background: 'rgba(255, 229, 92, 0.05)',
              border: '1px solid rgba(255, 229, 92, 0.2)',
              borderRadius: '12px',
              padding: '1.5rem',
              marginBottom: '2rem'
            }}
          >
            <h3 style={{ color: '#FFE55C', marginBottom: '1rem', fontSize: '1.2rem' }}>Infrastructure & Models</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', color: '#E0E0E0', fontSize: '0.95rem' }}>
              <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
                <h4 style={{ color: '#00E4BA', marginBottom: '0.5rem', fontSize: '1rem' }}>Falcon H1-34B</h4>
                <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
                  <strong>Hardware:</strong><br />
                  • 2x Nvidia A6000 48GB GPUs<br />
                  • 60 vCPUs<br />
                  • 116 GB RAM<br />
                  • 196 GB disk storage<br />
                  <br />
                  <strong>Software:</strong><br />
                  • PyTorch 2.4<br />
                  • CUDA 12.4
                </div>
              </div>

              <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
                <h4 style={{ color: '#00E4BA', marginBottom: '0.5rem', fontSize: '1rem' }}>EDU-Qwen2.5-7B (EduBench)</h4>
                <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
                  <strong>Hardware:</strong><br />
                  • 1x Nvidia A100 80GB GPU<br />
                  <br />
                  <strong>Hosting:</strong><br />
                  • HuggingFace Inference<br />
                  • Model: DirectionAI/EDU-Qwen2.5-7B<br />
                  <br />
                  <strong>Purpose:</strong><br />
                  • Educational question evaluation<br />
                  • Quality scoring across EC/IP/QA tasks
                </div>
              </div>
            </div>
            <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#888', fontStyle: 'italic' }}>
              Note: Current Falcon benchmarks reflect small-server performance. Production deployment with optimized infrastructure will significantly improve throughput and latency.
            </p>
          </motion.div>

          {/* Four Approaches Section */}
          <div style={{ marginBottom: '3rem' }}>
            <h3 style={{ color: '#00D4AA', fontSize: '1.5rem', marginBottom: '2rem', textAlign: 'center' }}>
              Our Four Approaches
            </h3>

            {approaches.map((approach, idx) => {
              const filteredData = getFilteredData(approach.id, approach.data);

              return (
                <div key={approach.id} style={{ marginBottom: '2rem' }}>
                  <motion.div
                    className="toggle-header"
                    onClick={() => toggleApproach(approach.id)}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    style={{
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '1rem',
                      padding: '1.25rem',
                      border: `2px solid ${approach.color}`,
                      borderRadius: '12px',
                      marginBottom: '1rem',
                      background: openApproaches[approach.id] ? `${approach.color}15` : 'rgba(255, 255, 255, 0.05)',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <h4 style={{ color: approach.color, margin: 0, fontSize: '1.2rem' }}>{approach.name}</h4>
                      <p style={{ color: '#B0B0B0', fontSize: '0.9rem', margin: '0.5rem 0 0 0' }}>{approach.description}</p>
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                        {approach.features.map((feature) => (
                          <span
                            key={feature}
                            style={{
                              fontSize: '0.75rem',
                              padding: '0.25rem 0.5rem',
                              background: `${approach.color}20`,
                              color: approach.color,
                              borderRadius: '4px',
                              border: `1px solid ${approach.color}40`
                            }}
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                    <motion.span
                      animate={{ rotate: openApproaches[approach.id] ? 180 : 0 }}
                      transition={{ duration: 0.3 }}
                      style={{ color: approach.color, fontSize: '1.5rem', flexShrink: 0 }}
                    >
                      ▼
                    </motion.span>
                  </motion.div>

                  <AnimatePresence>
                    {openApproaches[approach.id] && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.4, ease: 'easeInOut' }}
                        style={{ overflow: 'hidden' }}
                      >
                        {/* Search Box */}
                        <div style={{ marginBottom: '1rem', padding: '0 1rem' }}>
                          <input
                            type="text"
                            placeholder="Search benchmarks..."
                            value={searchTerms[approach.id]}
                            onChange={(e) => updateSearchTerm(approach.id, e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.75rem',
                              background: 'rgba(255, 255, 255, 0.05)',
                              border: `1px solid ${approach.color}40`,
                              borderRadius: '8px',
                              color: '#E0E0E0',
                              fontSize: '0.95rem',
                              outline: 'none'
                            }}
                            onFocus={(e) => e.target.style.borderColor = approach.color}
                            onBlur={(e) => e.target.style.borderColor = `${approach.color}40`}
                          />
                        </div>

                        <div className="benchmark-table-wrapper">
                          <table className="unified-benchmark-table">
                            <thead>
                              <tr>
                                <th>Subject</th>
                                <th>Skill</th>
                                <th>Topic</th>
                                <th>Grade</th>
                                <th>Count</th>
                                <th>P50</th>
                                <th>P90</th>
                                <th>P95</th>
                                <th>P99</th>
                                <th>Avg Time</th>
                                <th>EduBench EC</th>
                                <th>EduBench IP</th>
                                <th>EduBench QA</th>
                                <th>EduBench Overall</th>
                                <th>Arabic Similarity</th>
                                <th>Scaffolding Quality</th>
                                <th>Math Accuracy</th>
                                <th>Cultural Relevance</th>
                                <th>Image Quality</th>
                                <th>Multi-Modal</th>
                                <th>Error Rate</th>
                                <th>Cost</th>
                              </tr>
                            </thead>
                            <tbody>
                              {filteredData.length > 0 ? (
                                filteredData.map((row, index) => (
                                  <tr key={index}>
                                    <td>{row.subject}</td>
                                    <td>{row.skill}</td>
                                    <td>{row.topic || '—'}</td>
                                    <td>{row.grade}</td>
                                    <td>{row.count}</td>
                                    <td>{row.p50 || '—'}</td>
                                    <td>{row.p90}</td>
                                    <td>{row.p95}</td>
                                    <td>{row.p99}</td>
                                    <td>{row.avgTime || '—'}</td>
                                    <td>{row.eduBenchEC || '—'}</td>
                                    <td>{row.eduBenchIP || '—'}</td>
                                    <td>{row.eduBenchQA || '—'}</td>
                                    <td>{row.eduBenchOverall || '—'}</td>
                                    <td>{row.arabicSimilarity || '—'}</td>
                                    <td>{row.scaffoldingQuality || '—'}</td>
                                    <td>{row.mathAccuracy || '—'}</td>
                                    <td>{row.culturalRelevance || '—'}</td>
                                    <td>{row.imageQuality || '—'}</td>
                                    <td>{row.multiModal || '—'}</td>
                                    <td>{row.errorRate || '—'}</td>
                                    <td>{row.cost || '—'}</td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan={22} style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
                                    No results found for "{searchTerms[approach.id]}"
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}

            <p style={{ fontSize: '0.85rem', color: '#888', marginTop: '2rem', fontStyle: 'italic', lineHeight: '1.6' }}>
              <strong>Benchmark Columns Explained:</strong><br />
              <strong>Performance Metrics:</strong><br />
              • P50/P90/P95/P99: Performance percentiles for generation time<br />
              • Avg Time: Average generation time across all samples<br />
              • Error Rate: Percentage of failed or incomplete generations<br />
              • Cost: Estimated cost per question generation<br />
              <br />
              <strong>External Quality Benchmarks (EduBench):</strong><br />
              • EC (External Constraints): Adherence to curriculum standards and learning objectives<br />
              • IP (Item Prompt): Question clarity, appropriateness for grade level<br />
              • QA (Question Authoring): Overall authoring quality and pedagogical value<br />
              • Overall: Combined EduBench score across all task types<br />
              <br />
              <strong>Internal Quality Metrics:</strong><br />
              • Arabic Similarity: Linguistic authenticity compared to native Arabic educational content<br />
              • Scaffolding Quality: Pedagogical effectiveness of step-by-step explanations and hints<br />
              • Math Accuracy: Correctness of problems, solutions, and mathematical calculations<br />
              • Cultural Relevance: Alignment with UAE cultural context and examples<br />
              • Image Quality: Quality and relevance of generated educational diagrams/images<br />
              • Multi-Modal: Whether approach supports text + image generation<br />
              <br />
              • "—" indicates data collection in progress
            </p>
          </div>

        </div>
      </section>



      {/* FAQ and Email Signup Container */}
      <div className="faq-email-container">
        {/* FAQ Section */}
        <section id="faq-section" className="faq-section">
          <div className="section-content">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <h2 className="section-title">
                <span className="title-gradient">FAQ</span>
              </h2>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
              className="faq-list"
            >
              {[
                {
                  id: 'agentic',
                  question: 'What is the agentic approach?',
                  answer: 'Our system uses autonomous AI agents controlled by DSPy that can reason, plan, and execute complex educational content generation tasks. Each agent specializes in different aspects of question creation, working collaboratively under programmatic control.'
                },
                {
                  id: 'included',
                  question: "What's included with each question?",
                  answer: 'Every question comes with MCQ format, educational images/diagrams, 40-50 word step-by-step solutions, and plausible distractors based on common student errors.'
                },
                {
                  id: 'dspy',
                  question: 'How does DSPy control work?',
                  answer: 'DSPy provides programmatic control over our AI agents, enabling systematic prompt optimization, reliable agent coordination, and consistent output quality. It allows us to compose complex reasoning workflows while maintaining full observability and control over agent behavior.'
                },
                {
                  id: 'metrics',
                  question: 'How do performance metrics vary?',
                  answer: 'Performance depends on AI provider (OpenAI vs DSPy/Falcon), grade complexity (Grade 3 vs 8 vs 12), and batch size. DSPy-controlled agents offer better consistency and reproducibility, while direct API calls may be faster but less reliable.'
                },
                {
                  id: 'uae',
                  question: 'What makes this UAE-aligned?',
                  answer: 'Questions are fully aligned with UAE curriculum standards, support mixed Arabic-English text with proper mathematical notation, and include culturally relevant content.'
                },
                {
                  id: 'quality',
                  question: 'How is quality measured?',
                  answer: 'We use both external and internal benchmarks. External: EduBench measures question quality across EC (External Constraints/curriculum adherence), IP (Item Prompt/question clarity), and QA (Question Authoring) task types. Internal: We measure Arabic Similarity (how close generated content is to native Arabic), Scaffolding Quality (pedagogical effectiveness of step-by-step explanations), and Math Accuracy (correctness of problems and solutions).'
                },
                {
                  id: 'tech',
                  question: 'What are the core technologies?',
                  answer: 'DSPy framework for agent orchestration, advanced RAG for curriculum retrieval, multi-LLM provider support with automatic fallback, parallel agent execution with up to 20 workers, integrated multi-modal generation, and enterprise-grade system with robust failover capabilities.'
                },
                {
                  id: 'features',
                  question: 'What question features are included?',
                  answer: 'Complete step-by-step solutions, visual support with educational images and diagrams, MCQ conversion with plausible distractors, and mixed-script support for Arabic text with standard math notation.'
                },
                {
                  id: 'benchmarks',
                  question: 'What are the performance benchmarks?',
                  answer: 'Single agents complete questions in 2-3 minutes, but our parallel DSPy orchestration enables 10 questions in 4-5 minutes and 100 questions in ~20 minutes, with up to 20 autonomous agents executing simultaneously under programmatic control.'
                }
              ].map((faq) => (
                <div key={faq.id} className="faq-question">
                  <motion.div
                    className="faq-question-header"
                    onClick={() => toggleFAQ(faq.id)}
                    whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <h4>{faq.question}</h4>
                    <motion.span
                      animate={{ rotate: openFAQs[faq.id] ? 45 : 0 }}
                      transition={{ duration: 0.2 }}
                      className="faq-toggle"
                    >
                      +
                    </motion.span>
                  </motion.div>

                  <AnimatePresence>
                    {openFAQs[faq.id] && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                        className="faq-answer"
                      >
                        <p>{faq.answer}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Email Signup Section */}
        <section className="email-signup-section">
          <div className="email-signup-content">
            {/* Row 1: Title */}
            <motion.div
              className="signup-row signup-row-title"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <h2 className="section-title">
                <span className="title-gradient">Stay Connected</span>
              </h2>
            </motion.div>

            {/* Row 2: Email Forms */}
            <motion.div
              className="signup-row signup-row-forms"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <div className="signup-selector">
                <div className="signup-options">
                  <motion.div
                    className={`signup-option-card ${selectedSignupType === 'waitlist' ? 'active' : ''}`}
                    onClick={() => setSelectedSignupType('waitlist')}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="option-icon">🚀</div>
                    <h3 className="signup-option-title">Early Access</h3>
                    <p className="signup-option-description">Be first to try our agentic question generation</p>
                  </motion.div>

                  <motion.div
                    className={`signup-option-card ${selectedSignupType === 'newsletter' ? 'active' : ''}`}
                    onClick={() => setSelectedSignupType('newsletter')}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="option-icon">📧</div>
                    <h3 className="signup-option-title">Updates</h3>
                    <p className="signup-option-description">Get notified about our latest developments</p>
                  </motion.div>
                </div>

                <div className="signup-form-container">
                  <EmailOctopusForm
                    listType={selectedSignupType}
                    placeholder={selectedSignupType === 'waitlist' ? 'Join the waitlist' : 'Subscribe for updates'}
                  />
                </div>
              </div>
            </motion.div>

            <br />
            {/* Row 3: API Link */}
            <motion.div
              className="signup-row signup-row-actions"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              viewport={{ once: true }}
            >
              <a href="https://uae-poc.inceptapi.com/docs#" target="_blank" rel="noopener noreferrer" className="btn btn-api">
                <svg className="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Explore OpenAPI Reference
              </a>
            </motion.div>
          </div>
        </section>

      </div>

    </div>
  );
}

export default App;
