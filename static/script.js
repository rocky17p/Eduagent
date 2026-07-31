/**
 * AI Educational Content Generator (Part 2) - Frontend Logic
 * Handles form submission, API calls, and UI rendering
 * Updated for Part 2 schema with teacher notes and quantitative scores
 */

// DOM Elements
const generateForm = document.getElementById('generateForm');
const generateBtn = document.getElementById('generateBtn');
const btnText = generateBtn.querySelector('.btn-text');
const btnLoader = generateBtn.querySelector('.btn-loader');

// Output sections
const pipelineFlow = document.getElementById('pipelineFlow');
const generatorSection = document.getElementById('generatorSection');
const reviewerFlow = document.getElementById('reviewerFlow');
const reviewerSection = document.getElementById('reviewerSection');
const refinementFlow = document.getElementById('refinementFlow');
const refinedSection = document.getElementById('refinedSection');
const errorSection = document.getElementById('errorSection');

// Content containers
const explanationContent = document.getElementById('explanationContent');
const mcqsContent = document.getElementById('mcqsContent');
const reviewStatus = document.getElementById('reviewStatus');
const reviewerStatusBadge = document.getElementById('reviewerStatusBadge');
const feedbackContent = document.getElementById('feedbackContent');
const refinedExplanationContent = document.getElementById('refinedExplanationContent');
const refinedMcqsContent = document.getElementById('refinedMcqsContent');

/**
 * Set loading state for the generate button
 */
function setLoading(isLoading) {
    generateBtn.disabled = isLoading;
    btnText.style.display = isLoading ? 'none' : 'inline';
    btnLoader.style.display = isLoading ? 'inline-flex' : 'none';
}

/**
 * Hide all output sections
 */
function hideAllSections() {
    pipelineFlow.style.display = 'none';
    generatorSection.style.display = 'none';
    reviewerFlow.style.display = 'none';
    reviewerSection.style.display = 'none';
    refinementFlow.style.display = 'none';
    refinedSection.style.display = 'none';
    errorSection.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    hideAllSections();
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

/**
 * Extract text from explanation (handles both old and new schema)
 */
function getExplanationText(explanation) {
    if (typeof explanation === 'string') {
        return explanation;
    }
    if (explanation && typeof explanation === 'object') {
        return explanation.text || JSON.stringify(explanation);
    }
    return String(explanation);
}

/**
 * Render MCQs as cards (handles both old and new schema)
 */
function renderMCQs(mcqs, container) {
    container.innerHTML = mcqs.map((mcq, index) => {
        const optionLetters = ['A', 'B', 'C', 'D'];
        const optionsHTML = mcq.options.map((option, i) => {
            const letter = optionLetters[i];
            // Handle both old format (answer: "A") and new format (correct_index: 0)
            const correctIndex = mcq.correct_index !== undefined ? mcq.correct_index : optionLetters.indexOf(mcq.answer);
            const isCorrect = i === correctIndex;
            return `
                <div class="mcq-option ${isCorrect ? 'correct' : ''}">
                    <span class="option-letter">${letter}</span>
                    <span>${option}</span>
                </div>
            `;
        }).join('');

        return `
            <div class="mcq-card">
                <div class="mcq-question">Q${index + 1}: ${mcq.question}</div>
                <div class="mcq-options">${optionsHTML}</div>
            </div>
        `;
    }).join('');
}

/**
 * Render teacher notes section
 */
function renderTeacherNotes(teacherNotes) {
    if (!teacherNotes) return '';
    
    const misconceptionsList = (teacherNotes.common_misconceptions || [])
        .map(m => `<li>${m}</li>`)
        .join('');
    
    return `
        <div class="teacher-notes">
            <h4>📚 Teacher Notes</h4>
            <div class="teacher-notes-content">
                <p><strong>Learning Objective:</strong> ${teacherNotes.learning_objective || 'Not specified'}</p>
                ${misconceptionsList ? `
                <p><strong>Common Misconceptions:</strong></p>
                <ul>${misconceptionsList}</ul>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Render quantitative scores
 */
function renderScores(scores) {
    if (!scores) return '';
    
    const scoreItems = [
        { key: 'age_appropriateness', label: 'Age Appropriateness', emoji: '👶' },
        { key: 'correctness', label: 'Correctness', emoji: '✓' },
        { key: 'clarity', label: 'Clarity', emoji: '💡' },
        { key: 'coverage', label: 'Coverage', emoji: '📊' }
    ];
    
    return `
        <div class="scores-grid">
            ${scoreItems.map(item => {
                const score = scores[item.key] || 0;
                const scoreClass = score >= 4 ? 'high' : score >= 3 ? 'medium' : 'low';
                return `
                    <div class="score-item ${scoreClass}">
                        <span class="score-emoji">${item.emoji}</span>
                        <span class="score-label">${item.label}</span>
                        <span class="score-value">${score}/5</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Render feedback items (handles both old and new format)
 */
function renderFeedback(feedback) {
    if (!feedback || feedback.length === 0) {
        feedbackContent.innerHTML = '<p class="no-feedback">No specific feedback</p>';
        return;
    }
    
    feedbackContent.innerHTML = feedback.map(item => {
        // Handle both formats: string or {field, issue} object
        if (typeof item === 'string') {
            return `<div class="feedback-item">${item}</div>`;
        }
        return `
            <div class="feedback-item">
                <span class="feedback-field">${item.field || 'general'}</span>
                <span class="feedback-issue">${item.issue || item}</span>
            </div>
        `;
    }).join('');
}

/**
 * Display generator output with animation
 */
async function displayGeneratorOutput(data, container = null) {
    // Show pipeline flow
    pipelineFlow.style.display = 'flex';
    await sleep(200);
    
    // Determine which container to use
    const expContainer = container ? 
        container.querySelector('.explanation-content') || refinedExplanationContent : 
        explanationContent;
    const mcqContainer = container ? 
        container.querySelector('.mcqs-content') || refinedMcqsContent : 
        mcqsContent;
    
    if (!container) {
        generatorSection.style.display = 'block';
    }
    
    // Handle new explanation schema
    expContainer.textContent = getExplanationText(data.explanation);
    renderMCQs(data.mcqs || [], mcqContainer);
    
    // Add teacher notes if present
    if (data.teacher_notes && !container) {
        const teacherNotesHTML = renderTeacherNotes(data.teacher_notes);
        const existingNotes = document.getElementById('teacherNotesSection');
        if (existingNotes) {
            existingNotes.innerHTML = teacherNotesHTML;
        } else {
            const notesDiv = document.createElement('div');
            notesDiv.id = 'teacherNotesSection';
            notesDiv.innerHTML = teacherNotesHTML;
            mcqsContent.parentNode.insertBefore(notesDiv, mcqsContent.nextSibling);
        }
    }
}

/**
 * Display reviewer output with animation
 */
async function displayReviewerOutput(data) {
    // Show reviewer flow arrow
    reviewerFlow.style.display = 'flex';
    await sleep(200);
    
    // Show reviewer section
    reviewerSection.style.display = 'block';
    
    // Handle both old (status) and new (passed) format
    const isPassing = data.passed === true || data.status === 'pass';
    reviewStatus.className = `review-status ${isPassing ? 'pass' : 'fail'}`;
    
    // Include scores if available
    const scoresHTML = data.scores ? renderScores(data.scores) : '';
    
    reviewStatus.innerHTML = `
        <span class="review-status-icon">${isPassing ? '✅' : '❌'}</span>
        <span>Status: ${isPassing ? 'Content Approved' : 'Needs Improvement'}</span>
        ${scoresHTML}
    `;
    
    reviewerStatusBadge.textContent = isPassing ? 'Passed' : 'Failed';
    reviewerStatusBadge.style.background = isPassing ? 'var(--success-bg)' : 'var(--error-bg)';
    reviewerStatusBadge.style.color = isPassing ? 'var(--success)' : 'var(--error)';
    reviewerStatusBadge.style.borderColor = isPassing ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)';
    
    renderFeedback(data.feedback);
}

/**
 * Display refined output with animation
 */
async function displayRefinedOutput(data) {
    // Show refinement flow arrow
    refinementFlow.style.display = 'flex';
    await sleep(200);
    
    // Show refined section
    refinedSection.style.display = 'block';
    refinedExplanationContent.textContent = getExplanationText(data.explanation);
    renderMCQs(data.mcqs || [], refinedMcqsContent);
}

/**
 * Utility function for adding delays
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Main form submission handler
 */
generateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const grade = document.getElementById('grade').value;
    const topic = document.getElementById('topic').value.trim();
    
    if (!grade || !topic) {
        showError('Please fill in both grade and topic fields.');
        return;
    }
    
    // Reset UI
    hideAllSections();
    setLoading(true);
    
    try {
        // Call the API
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ grade: parseInt(grade), topic }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate content');
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Unknown error occurred');
        }
        
        // Store the full artifact for debugging
        window.lastResult = data;
        console.log('📦 Full RunArtifact:', data.run_artifact);
        
        // Display results with animations
        await displayGeneratorOutput(data.generator_output);
        await sleep(300);
        
        await displayReviewerOutput(data.reviewer_output);
        await sleep(300);
        
        // Show refined output if content was refined
        if (data.was_refined && data.refined_output) {
            await displayRefinedOutput(data.refined_output);
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred. Please try again.');
    } finally {
        setLoading(false);
    }
});

// Smooth scroll to results when they appear
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -10% 0px'
};

const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
}, observerOptions);

// Observe output sections for smooth scrolling
[generatorSection, reviewerSection, refinedSection].forEach(section => {
    scrollObserver.observe(section);
});

// Log health check on load
fetch('/api/health')
    .then(res => res.json())
    .then(health => {
        console.log('🎓 EduAgent - Health Check:', health);
        if (!health.has_api_key) {
            console.log('ℹ️ Running with mock responses (no API key)');
        }
    })
    .catch(err => console.log('Health check failed:', err));

// ==================== History Tab Functionality ====================

/**
 * Tab switching
 */
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update button states
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show/hide tabs
        const tabName = btn.dataset.tab;
        document.getElementById('generateTab').style.display = tabName === 'generate' ? 'block' : 'none';
        document.getElementById('historyTab').style.display = tabName === 'history' ? 'block' : 'none';
        
        // Load history when switching to history tab
        if (tabName === 'history') {
            loadHistory();
        }
    });
});

/**
 * Load history from API
 */
async function loadHistory() {
    const container = document.getElementById('historyContainer');
    container.innerHTML = '<p class="loading-text">Loading history...</p>';
    
    try {
        const response = await fetch('/api/history?limit=20');
        const data = await response.json();
        
        if (!data.success || data.artifacts.length === 0) {
            container.innerHTML = '<p class="no-history">No generation history yet. Generate some content first!</p>';
            return;
        }
        
        // Store artifacts for detail view
        window.historyArtifacts = {};
        data.artifacts.forEach(a => window.historyArtifacts[a.run_id] = a);
        
        container.innerHTML = data.artifacts.map(artifact => {
            const status = artifact.final?.status || 'unknown';
            const statusClass = status === 'approved' ? 'approved' : 'rejected';
            const attempts = artifact.attempts?.length || 0;
            const timestamp = artifact.timestamps?.started_at ? 
                new Date(artifact.timestamps.started_at).toLocaleString() : 'Unknown';
            
            return `
                <div class="history-item ${statusClass}" onclick="toggleArtifactDetail('${artifact.run_id}')">
                    <div class="history-header">
                        <span class="history-topic">${artifact.input?.topic || 'Unknown topic'}</span>
                        <span class="history-status ${statusClass}">${status.toUpperCase()}</span>
                    </div>
                    <div class="history-meta">
                        <span>Grade ${artifact.input?.grade || '?'}</span>
                        <span>•</span>
                        <span>${attempts} attempt${attempts !== 1 ? 's' : ''}</span>
                        <span>•</span>
                        <span>${timestamp}</span>
                    </div>
                    <div class="history-run-id">Run ID: ${artifact.run_id}</div>
                    <div class="history-expand-hint">Click to view details ▼</div>
                    <div class="artifact-detail" id="detail-${artifact.run_id}" style="display: none;"></div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        container.innerHTML = `<p class="error-text">Error loading history: ${error.message}</p>`;
    }
}

/**
 * Toggle artifact detail view
 */
function toggleArtifactDetail(runId) {
    const detailDiv = document.getElementById(`detail-${runId}`);
    
    if (detailDiv.style.display === 'none') {
        // Show details
        const artifact = window.historyArtifacts[runId];
        detailDiv.innerHTML = renderArtifactDetail(artifact);
        detailDiv.style.display = 'block';
    } else {
        // Hide details
        detailDiv.style.display = 'none';
    }
}

/**
 * Render full artifact detail
 */
function renderArtifactDetail(artifact) {
    if (!artifact) return '<p>No data available</p>';
    
    const finalContent = artifact.final?.content;
    const tags = artifact.final?.tags;
    const attempts = artifact.attempts || [];
    
    let html = '<div class="artifact-detail-content">';
    
    // Attempts section
    html += '<div class="detail-section"><h4>📊 Pipeline Attempts</h4>';
    attempts.forEach((attempt, i) => {
        const review = attempt.review || {};
        const passed = review.passed ? '✅ Passed' : '❌ Failed';
        const scores = review.scores || {};
        
        html += `
            <div class="attempt-card">
                <div class="attempt-header">Attempt ${attempt.attempt} - ${passed}</div>
                ${review.scores ? `
                <div class="attempt-scores">
                    <span class="mini-score">Age: ${scores.age_appropriateness || '-'}/5</span>
                    <span class="mini-score">Correct: ${scores.correctness || '-'}/5</span>
                    <span class="mini-score">Clarity: ${scores.clarity || '-'}/5</span>
                    <span class="mini-score">Coverage: ${scores.coverage || '-'}/5</span>
                </div>` : ''}
                ${review.feedback && review.feedback.length > 0 ? `
                <div class="attempt-feedback">
                    <strong>Feedback:</strong>
                    <ul>${review.feedback.map(f => 
                        `<li><code>${f.field || 'general'}</code>: ${f.issue || f}</li>`
                    ).join('')}</ul>
                </div>` : ''}
            </div>
        `;
    });
    html += '</div>';
    
    // Final content (if approved)
    if (finalContent) {
        const explanation = finalContent.explanation;
        const explanationText = typeof explanation === 'string' ? explanation : (explanation?.text || '');
        const mcqs = finalContent.mcqs || [];
        const teacherNotes = finalContent.teacher_notes || {};
        
        html += '<div class="detail-section"><h4>📚 Generated Content</h4>';
        html += `<div class="detail-explanation">${explanationText}</div>`;
        
        // MCQs
        if (mcqs.length > 0) {
            html += '<div class="detail-mcqs"><strong>MCQs:</strong><ol>';
            mcqs.forEach(mcq => {
                const correctIdx = mcq.correct_index !== undefined ? mcq.correct_index : 0;
                html += `<li><strong>${mcq.question}</strong><br>`;
                mcq.options.forEach((opt, i) => {
                    const marker = i === correctIdx ? '✓ ' : '';
                    const style = i === correctIdx ? 'color: var(--success);' : '';
                    html += `<span style="${style}">${marker}${String.fromCharCode(65 + i)}) ${opt}</span><br>`;
                });
                html += '</li>';
            });
            html += '</ol></div>';
        }
        
        // Teacher Notes
        if (teacherNotes.learning_objective) {
            html += `<div class="detail-teacher-notes">
                <strong>📖 Teacher Notes:</strong><br>
                <em>Objective:</em> ${teacherNotes.learning_objective}<br>
                ${teacherNotes.common_misconceptions ? 
                    `<em>Common Misconceptions:</em><ul>${teacherNotes.common_misconceptions.map(m => `<li>${m}</li>`).join('')}</ul>` : ''}
            </div>`;
        }
        html += '</div>';
    }
    
    // Tags (if approved)
    if (tags) {
        html += `<div class="detail-section"><h4>🏷️ Tags</h4>
            <div class="detail-tags">
                <span class="tag">Subject: ${tags.subject}</span>
                <span class="tag">Difficulty: ${tags.difficulty}</span>
                <span class="tag">Bloom's: ${tags.blooms_level}</span>
                <span class="tag">Types: ${(tags.content_type || []).join(', ')}</span>
            </div>
        </div>`;
    }
    
    // Timestamps
    html += `<div class="detail-section"><h4>⏱️ Timestamps</h4>
        <div class="detail-timestamps">
            <span>Started: ${artifact.timestamps?.started_at || '-'}</span>
            <span>Finished: ${artifact.timestamps?.finished_at || '-'}</span>
        </div>
    </div>`;
    
    html += '</div>';
    return html;
}

/**
 * Refresh history button
 */
document.getElementById('refreshHistory')?.addEventListener('click', loadHistory);


