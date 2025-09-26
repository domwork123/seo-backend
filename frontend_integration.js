// Frontend Integration for Query Visibility Checker
// Add this code to your Lovable dashboard

// API Configuration
const API_BASE_URL = 'https://web-production-a5831.up.railway.app';

// Query Visibility Checker Integration
class QueryVisibilityChecker {
    constructor() {
        this.currentStep = 1;
        this.analysisData = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateUI();
    }

    setupEventListeners() {
        // Get Company Information button
        const getCompanyBtn = document.querySelector('[data-action="get-company-info"]');
        if (getCompanyBtn) {
            getCompanyBtn.addEventListener('click', () => this.startAnalysis());
        }

        // Domain input field
        const domainInput = document.querySelector('[data-input="domain"]');
        if (domainInput) {
            domainInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.startAnalysis();
                }
            });
        }
    }

    async startAnalysis() {
        const domainInput = document.querySelector('[data-input="domain"]');
        const url = domainInput?.value?.trim();
        
        if (!url) {
            this.showError('Please enter a valid domain');
            return;
        }

        // Add protocol if missing
        const fullUrl = url.startsWith('http') ? url : `https://${url}`;
        
        this.showLoading();
        
        try {
            console.log('Starting query visibility analysis for:', fullUrl);
            
            const response = await fetch(`${API_BASE_URL}/query-check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: fullUrl,
                    queries: [] // Let the backend generate queries automatically
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Query analysis response:', data);
            
            this.handleAnalysisResponse(data);
            
        } catch (error) {
            console.error('Query analysis failed:', error);
            this.showError(`Analysis failed: ${error.message}`);
        }
    }

    handleAnalysisResponse(data) {
        if (data.error) {
            this.showError(data.error);
            return;
        }

        const analysis = data.query_analysis;
        if (!analysis.success) {
            this.showError('Analysis failed to complete');
            return;
        }

        this.analysisData = analysis;
        this.currentStep = 2; // Move to Brand step
        this.updateUI();
        this.displayBrandInfo();
    }

    displayBrandInfo() {
        const context = this.analysisData.context;
        
        // Update Brand step with extracted information
        this.updateBrandStep({
            brandName: context.brand_name,
            description: context.description,
            industry: context.industry,
            location: context.location,
            products: context.products,
            faqTopics: context.faq_topics
        });

        // Move to Queries step
        setTimeout(() => {
            this.currentStep = 3;
            this.updateUI();
            this.displayQueries();
        }, 2000);
    }

    displayQueries() {
        const results = this.analysisData.results;
        
        // Update Queries step with generated queries and AI responses
        this.updateQueriesStep(results);

        // Move to Results step
        setTimeout(() => {
            this.currentStep = 4;
            this.updateUI();
            this.displayResults();
        }, 2000);
    }

    displayResults() {
        const results = this.analysisData.results;
        
        // Update Results step with analysis and recommendations
        this.updateResultsStep(results);
    }

    updateBrandStep(brandInfo) {
        // Update the Brand step UI with extracted information
        const brandStep = document.querySelector('[data-step="brand"]');
        if (brandStep) {
            brandStep.innerHTML = `
                <div class="brand-info">
                    <h3>Brand Information Extracted</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Brand Name:</label>
                            <span>${brandInfo.brandName}</span>
                        </div>
                        <div class="info-item">
                            <label>Industry:</label>
                            <span>${brandInfo.industry}</span>
                        </div>
                        <div class="info-item">
                            <label>Location:</label>
                            <span>${brandInfo.location || 'Not specified'}</span>
                        </div>
                        <div class="info-item">
                            <label>Description:</label>
                            <span>${brandInfo.description.substring(0, 200)}...</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    updateQueriesStep(results) {
        // Update the Queries step UI with generated queries
        const queriesStep = document.querySelector('[data-step="queries"]');
        if (queriesStep) {
            const queriesList = results.map((result, index) => `
                <div class="query-item">
                    <div class="query-number">${index + 1}</div>
                    <div class="query-content">
                        <div class="query-text">"${result.query}"</div>
                        <div class="query-status ${result.brand_mentioned ? 'mentioned' : 'not-mentioned'}">
                            ${result.brand_mentioned ? '✅ Brand Mentioned' : '❌ Brand Not Mentioned'}
                        </div>
                    </div>
                </div>
            `).join('');

            queriesStep.innerHTML = `
                <div class="queries-info">
                    <h3>Generated Queries & AI Responses</h3>
                    <div class="queries-list">
                        ${queriesList}
                    </div>
                </div>
            `;
        }
    }

    updateResultsStep(results) {
        // Update the Results step UI with analysis and recommendations
        const resultsStep = document.querySelector('[data-step="results"]');
        if (resultsStep) {
            const brandMentionedCount = results.filter(r => r.brand_mentioned).length;
            const totalQueries = results.length;
            const visibilityScore = Math.round((brandMentionedCount / totalQueries) * 100);

            const recommendationsList = results
                .filter(r => !r.brand_mentioned || r.competitors_mentioned.length > 0)
                .map(result => `
                    <div class="recommendation-item">
                        <div class="recommendation-query">"${result.query}"</div>
                        <div class="recommendation-text">${result.recommendation}</div>
                        <div class="competitors">
                            ${result.competitors_mentioned.length > 0 ? 
                                `Competitors mentioned: ${result.competitors_mentioned.join(', ')}` : 
                                'No competitors mentioned'
                            }
                        </div>
                    </div>
                `).join('');

            resultsStep.innerHTML = `
                <div class="results-info">
                    <div class="score-summary">
                        <h3>Query Visibility Analysis</h3>
                        <div class="score-circle">
                            <div class="score-number">${visibilityScore}%</div>
                            <div class="score-label">Brand Visibility</div>
                        </div>
                        <div class="score-breakdown">
                            <div class="breakdown-item">
                                <span>Brand Mentioned:</span>
                                <span>${brandMentionedCount}/${totalQueries} queries</span>
                            </div>
                            <div class="breakdown-item">
                                <span>Missing Opportunities:</span>
                                <span>${totalQueries - brandMentionedCount} queries</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="recommendations">
                        <h4>Actionable Recommendations</h4>
                        <div class="recommendations-list">
                            ${recommendationsList}
                        </div>
                    </div>
                </div>
            `;
        }
    }

    updateUI() {
        // Update step indicators
        const steps = document.querySelectorAll('[data-step-indicator]');
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            if (stepNumber < this.currentStep) {
                step.classList.add('completed');
            } else if (stepNumber === this.currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    }

    showLoading() {
        const loadingElement = document.querySelector('[data-loading]');
        if (loadingElement) {
            loadingElement.style.display = 'block';
            loadingElement.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <div class="loading-text">Analyzing website and generating queries...</div>
                </div>
            `;
        }
    }

    showError(message) {
        const errorElement = document.querySelector('[data-error]');
        if (errorElement) {
            errorElement.style.display = 'block';
            errorElement.innerHTML = `
                <div class="error-message">
                    <div class="error-icon">⚠️</div>
                    <div class="error-text">${message}</div>
                </div>
            `;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new QueryVisibilityChecker();
});

// Export for use in other components
window.QueryVisibilityChecker = QueryVisibilityChecker;
