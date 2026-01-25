/**
 * AI Educational Content Generator - Frontend Logic
 * Handles form submission, API calls, and UI rendering
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
 * Render MCQs as cards
 */
function renderMCQs(mcqs, container) {
    container.innerHTML = mcqs.map((mcq, index) => {
        const optionLetters = ['A', 'B', 'C', 'D'];
        const optionsHTML = mcq.options.map((option, i) => {
            const letter = optionLetters[i];
            const isCorrect = mcq.answer === letter || mcq.answer === option;
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
 * Render feedback items
 */
function renderFeedback(feedback) {
    feedbackContent.innerHTML = feedback.map(item => `
        <div class="feedback-item">${item}</div>
    `).join('');
}

/**
 * Display generator output with animation
 */
async function displayGeneratorOutput(data) {
    // Show pipeline flow
    pipelineFlow.style.display = 'flex';
    await sleep(200);
    
    // Show generator section
    generatorSection.style.display = 'block';
    explanationContent.textContent = data.explanation;
    renderMCQs(data.mcqs, mcqsContent);
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
    
    const isPassing = data.status === 'pass';
    reviewStatus.className = `review-status ${data.status}`;
    reviewStatus.innerHTML = `
        <span class="review-status-icon">${isPassing ? '✅' : '❌'}</span>
        <span>Status: ${isPassing ? 'Content Approved' : 'Needs Improvement'}</span>
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
    refinedExplanationContent.textContent = data.explanation;
    renderMCQs(data.mcqs, refinedMcqsContent);
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
        console.log('🎓 EduGen AI - Health Check:', health);
        if (!health.has_api_key) {
            console.log('ℹ️ Running with mock responses (no API key)');
        }
    })
    .catch(err => console.log('Health check failed:', err));
