// Admin Interface JavaScript

// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
    initializeDataTables();
});

// Initialize Chart.js charts
function initializeCharts() {
    // Check if charts container exists
    const chartsContainer = document.getElementById('charts-container');
    if (!chartsContainer) return;

    // Request Volume Chart
    const requestVolumeCtx = document.getElementById('requestVolumeChart');
    if (requestVolumeCtx) {
        new Chart(requestVolumeCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Request Volume',
                    data: [120, 150, 180, 140, 200, 90, 70],
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(17, 24, 39, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(59, 130, 246, 0.5)',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Category Breakdown Chart
    const categoryBreakdownCtx = document.getElementById('categoryBreakdownChart');
    if (categoryBreakdownCtx) {
        new Chart(categoryBreakdownCtx, {
            type: 'doughnut',
            data: {
                labels: ['Technical', 'Billing', 'Account', 'General'],
                datasets: [{
                    data: [45, 25, 20, 10],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(107, 114, 128, 0.8)'
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${percentage}% (${value})`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Resolution Trends Chart
    const resolutionTrendsCtx = document.getElementById('resolutionTrendsChart');
    if (resolutionTrendsCtx) {
        new Chart(resolutionTrendsCtx, {
            type: 'bar',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [
                    {
                        label: 'Resolved',
                        data: [85, 87, 89, 91],
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Escalated',
                        data: [15, 13, 11, 9],
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: 'rgba(239, 68, 68, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    },
                    x: {
                        stacked: true,
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Agent Performance Chart
    const agentPerformanceCtx = document.getElementById('agentPerformanceChart');
    if (agentPerformanceCtx) {
        new Chart(agentPerformanceCtx, {
            type: 'radar',
            data: {
                labels: ['Accuracy', 'Speed', 'Resolution Rate', 'Customer Satisfaction', 'Knowledge'],
                datasets: [{
                    label: 'Current',
                    data: [90, 85, 82, 88, 75],
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)'
                }, {
                    label: 'Team Average',
                    data: [80, 70, 75, 80, 85],
                    backgroundColor: 'rgba(156, 163, 175, 0.2)',
                    borderColor: 'rgba(156, 163, 175, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(156, 163, 175, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: {
                            display: true,
                            color: 'rgba(156, 163, 175, 0.2)'
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                }
            }
        });
    }
}

// Setup event listeners
function setupEventListeners() {
    // Provider test buttons
    const testButtons = document.querySelectorAll('[id^="test-"]');
    testButtons.forEach(button => {
        button.addEventListener('click', function() {
            const providerName = this.id.replace('test-', '');
            testProvider(providerName, this);
        });
    });

    // Toggle provider buttons
    const toggleButtons = document.querySelectorAll('[id^="toggle-"]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const providerName = this.id.replace('toggle-', '');
            toggleProvider(providerName);
        });
    });

    // Date range selectors
    const dateRangeSelectors = document.querySelectorAll('.date-range-selector');
    dateRangeSelectors.forEach(selector => {
        selector.addEventListener('change', function() {
            updateDateRange(this.value);
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
            }
        });
    });

    // Provider type selection
    const providerTypeSelect = document.getElementById('provider_type');
    if (providerTypeSelect) {
        providerTypeSelect.addEventListener('change', updateProviderFields);
    }
}

// Test provider connection
async function testProvider(providerName, button) {
    // Save original button content
    const originalContent = button.innerHTML;
    
    // Update button to show testing state
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    button.disabled = true;

    try {
        // Make API request to test provider
        const response = await fetch(`/admin/integrations/${providerName}/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        // Update button based on result
        if (data.status === 'success') {
            button.innerHTML = '<i class="fas fa-check text-green-600"></i> Success';
            button.className = button.className.replace('bg-blue-100', 'bg-green-100').replace('text-blue-800', 'text-green-800');
        } else {
            button.innerHTML = '<i class="fas fa-times text-red-600"></i> Failed';
            button.className = button.className.replace('bg-blue-100', 'bg-red-100').replace('text-blue-800', 'text-red-800');
        }
        
        // Reset button after delay
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
            button.className = button.className.replace('bg-green-100', 'bg-blue-100').replace('bg-red-100', 'bg-blue-100').replace('text-green-800', 'text-blue-800').replace('text-red-800', 'text-blue-800');
        }, 3000);
        
    } catch (error) {
        console.error('Error testing provider:', error);
        button.innerHTML = '<i class="fas fa-times text-red-600"></i> Error';
        button.className = button.className.replace('bg-blue-100', 'bg-red-100').replace('text-blue-800', 'text-red-800');
        
        // Reset button after delay
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
            button.className = button.className.replace('bg-red-100', 'bg-blue-100').replace('text-red-800', 'text-blue-800');
        }, 3000);
    }
}

// Toggle provider enabled status
async function toggleProvider(providerName) {
    try {
        const response = await fetch(`/admin/integrations/${providerName}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Reload page to reflect changes
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error toggling provider:', error);
        alert('Error: ' + error);
    }
}

// Update date range for analytics
function updateDateRange(range) {
    // This would typically make an API call to get new data
    console.log('Updating date range to:', range);
    
    // For demo, we'll just show a loading state
    const chartsContainer = document.getElementById('charts-container');
    if (chartsContainer) {
        chartsContainer.classList.add('opacity-50');
        
        // Simulate loading
        setTimeout(() => {
            chartsContainer.classList.remove('opacity-50');
            // Would update charts with new data here
        }, 1000);
    }
}

// Form validation
function validateForm(form) {
    let valid = true;
    
    // Check required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('border-red-500');
            
            // Add error message if it doesn't exist
            let errorMsg = field.parentNode.querySelector('.error-message');
            if (!errorMsg) {
                errorMsg = document.createElement('p');
                errorMsg.className = 'text-red-500 text-xs mt-1 error-message';
                errorMsg.textContent = 'This field is required';
                field.parentNode.appendChild(errorMsg);
            }
            
            valid = false;
        } else {
            field.classList.remove('border-red-500');
            
            // Remove error message if it exists
            const errorMsg = field.parentNode.querySelector('.error-message');
            if (errorMsg) {
                errorMsg.remove();
            }
        }
    });
    
    // Validate email fields
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value.trim() && !validateEmail(field.value)) {
            field.classList.add('border-red-500');
            
            // Add error message if it doesn't exist
            let errorMsg = field.parentNode.querySelector('.error-message');
            if (!errorMsg) {
                errorMsg = document.createElement('p');
                errorMsg.className = 'text-red-500 text-xs mt-1 error-message';
                errorMsg.textContent = 'Please enter a valid email address';
                field.parentNode.appendChild(errorMsg);
            }
            
            valid = false;
        }
    });
    
    return valid;
}

// Email validation helper
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Update provider fields based on selection
function updateProviderFields() {
    const providerType = document.getElementById('provider_type').value;
    const fieldsContainer = document.getElementById('provider-fields');
    
    const fieldConfigs = {
        'salesforce': [
            {name: 'api_key', label: 'Client ID', type: 'text', required: true},
            {name: 'api_secret', label: 'Client Secret', type: 'password', required: true},
            {name: 'username', label: 'Username', type: 'text', required: true},
            {name: 'password', label: 'Password', type: 'password', required: true}
        ],
        'hubspot': [
            {name: 'api_key', label: 'API Key', type: 'password', required: true}
        ],
        'zendesk': [
            {name: 'username', label: 'Email', type: 'email', required: true},
            {name: 'api_key', label: 'API Token', type: 'password', required: true}
        ],
        'shopify': [
            {name: 'api_key', label: 'Access Token', type: 'password', required: true}
        ],
        'postgresql': [
            {name: 'database_url', label: 'Database URL', type: 'text', required: true}
        ]
    };
    
    const fields = fieldConfigs[providerType] || [];
    
    fieldsContainer.innerHTML = '';
    
    if (fields.length > 0) {
        const gridDiv = document.createElement('div');
        gridDiv.className = 'grid grid-cols-1 md:grid-cols-2 gap-6';
        
        fields.forEach(field => {
            const fieldDiv = document.createElement('div');
            fieldDiv.innerHTML = `
                <label for="${field.name}" class="block text-sm font-medium text-gray-700">${field.label}</label>
                <input type="${field.type}" name="${field.name}" id="${field.name}" ${field.required ? 'required' : ''}
                       class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm">
            `;
            gridDiv.appendChild(fieldDiv);
        });
        
        fieldsContainer.appendChild(gridDiv);
    }
}

// Initialize DataTables
function initializeDataTables() {
    // Check if DataTables is available
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'pdf', 'print'
            ]
        });
    }
}