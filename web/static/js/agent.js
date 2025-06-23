// Agent Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeAgentDashboard();
    setupChatInterface();
    initializeWebSocket();
    setupQueueManagement();
    setupCustomerProfileView();
});

// Initialize agent dashboard
function initializeAgentDashboard() {
    const statusSelector = document.getElementById('agentStatusSelector');
    if (statusSelector) {
        statusSelector.addEventListener('change', function() {
            updateAgentStatus(this.value);
        });
    }
    
    // Initialize charts if they exist
    initializeAgentCharts();
}

// Initialize agent performance charts
function initializeAgentCharts() {
    const performanceChartEl = document.getElementById('agentPerformanceChart');
    if (!performanceChartEl) return;
    
    const ctx = performanceChartEl.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Resolved Tickets',
                data: [5, 8, 6, 9, 12, 4, 7],
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // Satisfaction chart
    const satisfactionChartEl = document.getElementById('satisfactionChart');
    if (satisfactionChartEl) {
        const ctx = satisfactionChartEl.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Excellent', 'Good', 'Average', 'Poor'],
                datasets: [{
                    data: [65, 20, 10, 5],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Update agent status
async function updateAgentStatus(status) {
    try {
        // In a real implementation, this would make an API call
        console.log('Updating agent status to:', status);
        
        // Update UI to reflect status change
        const statusIndicator = document.getElementById('statusIndicator');
        if (statusIndicator) {
            // Remove all status classes
            statusIndicator.classList.remove('bg-green-100', 'text-green-800', 'bg-red-100', 'text-red-800', 'bg-yellow-100', 'text-yellow-800', 'bg-gray-100', 'text-gray-800');
            
            // Add appropriate class based on status
            switch (status) {
                case 'available':
                    statusIndicator.classList.add('bg-green-100', 'text-green-800');
                    statusIndicator.innerHTML = '<span class="h-2 w-2 mr-1 bg-green-400 rounded-full"></span> Available';
                    break;
                case 'busy':
                    statusIndicator.classList.add('bg-red-100', 'text-red-800');
                    statusIndicator.innerHTML = '<span class="h-2 w-2 mr-1 bg-red-400 rounded-full"></span> Busy';
                    break;
                case 'away':
                    statusIndicator.classList.add('bg-yellow-100', 'text-yellow-800');
                    statusIndicator.innerHTML = '<span class="h-2 w-2 mr-1 bg-yellow-400 rounded-full"></span> Away';
                    break;
                case 'offline':
                    statusIndicator.classList.add('bg-gray-100', 'text-gray-800');
                    statusIndicator.innerHTML = '<span class="h-2 w-2 mr-1 bg-gray-400 rounded-full"></span> Offline';
                    break;
            }
        }
        
        // Send status update via WebSocket
        if (window.agentSocket && window.agentSocket.readyState === WebSocket.OPEN) {
            window.agentSocket.send(JSON.stringify({
                type: 'status_update',
                status: status
            }));
        }
        
    } catch (error) {
        console.error('Error updating status:', error);
        alert('Failed to update status. Please try again.');
    }
}

// Setup chat interface
function setupChatInterface() {
    const chatForm = document.getElementById('agentChatForm');
    if (!chatForm) return;
    
    const messageInput = document.getElementById('agentMessageInput');
    const chatMessages = document.getElementById('agentChatMessages');
    const agentId = document.getElementById('agentId')?.value || 'unknown';
    const conversationId = document.getElementById('conversationId')?.value || 'unknown';
    
    // Function to add message to chat
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'mb-4 ' + (sender === 'agent' ? 'ml-auto max-w-3/4' : '');
        
        if (sender === 'agent') {
            messageDiv.innerHTML = `
                <div class="flex justify-end">
                    <div class="bg-blue-100 p-3 rounded-lg">
                        <p class="text-sm">${message}</p>
                        <p class="text-xs text-gray-500 mt-1 text-right">You - Just now</p>
                    </div>
                </div>
            `;
        } else if (sender === 'customer') {
            messageDiv.innerHTML = `
                <div class="flex">
                    <div class="bg-gray-100 p-3 rounded-lg">
                        <p class="text-sm">${message}</p>
                        <p class="text-xs text-gray-500 mt-1">Customer - Just now</p>
                    </div>
                </div>
            `;
        } else if (sender === 'system') {
            messageDiv.innerHTML = `
                <div class="flex justify-center">
                    <div class="bg-yellow-50 p-2 rounded-lg text-center">
                        <p class="text-xs text-yellow-800">${message}</p>
                    </div>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add agent message to chat
        addMessage(message, 'agent');
        
        // Clear input
        messageInput.value = '';
        
        // Send message to server
        sendAgentMessage(message);
    });
    
    // Function to send agent message
    async function sendAgentMessage(message) {
        try {
            // In a real implementation, this would make an API call
            console.log('Sending agent message:', message);
            
            // Simulate customer response after delay
            setTimeout(() => {
                const responses = [
                    "Thank you for the information. That helps a lot.",
                    "I understand now. Could you explain a bit more about the next steps?",
                    "That makes sense. I'll try what you suggested.",
                    "I appreciate your help with this issue."
                ];
                
                const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                addMessage(randomResponse, 'customer');
            }, 2000);
            
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('Error sending message. Please try again.', 'system');
        }
    }
    
    // Quick response buttons
    const quickResponseButtons = document.querySelectorAll('.quick-response-btn');
    quickResponseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const responseText = this.dataset.response;
            messageInput.value = responseText;
            messageInput.focus();
        });
    });
    
    // Canned responses dropdown
    const cannedResponseSelect = document.getElementById('cannedResponseSelect');
    if (cannedResponseSelect) {
        cannedResponseSelect.addEventListener('change', function() {
            if (this.value) {
                messageInput.value = this.value;
                messageInput.focus();
                this.selectedIndex = 0; // Reset dropdown
            }
        });
    }
}

// Initialize WebSocket connection
function initializeWebSocket() {
    const agentId = document.getElementById('agentId')?.value || 'unknown';
    
    // Create WebSocket connection
    const socket = new WebSocket(`ws://${window.location.host}/agent/ws/${agentId}`);
    
    socket.onopen = function(e) {
        console.log('WebSocket connection established');
        window.agentSocket = socket;
    };
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    socket.onclose = function(event) {
        console.log('WebSocket connection closed');
        // Attempt to reconnect after delay
        setTimeout(() => {
            initializeWebSocket();
        }, 5000);
    };
    
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    console.log('Received WebSocket message:', data);
    
    switch (data.type) {
        case 'new_ticket':
            notifyNewTicket(data.data);
            break;
        case 'customer_message':
            handleCustomerMessage(data.data);
            break;
        case 'ticket_assigned':
            notifyTicketAssigned(data.data);
            break;
        case 'status_update':
            updateAgentStatusUI(data.agent_id, data.status);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// Notify about new ticket
function notifyNewTicket(ticketData) {
    // Create notification
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-4 w-80 border-l-4 border-blue-500 animate-slide-in';
    notification.innerHTML = `
        <div class="flex justify-between items-start">
            <div>
                <h4 class="text-sm font-medium text-gray-900">New Ticket Available</h4>
                <p class="text-xs text-gray-600 mt-1">${ticketData.subject}</p>
                <p class="text-xs text-gray-500 mt-1">Priority: ${ticketData.priority}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-500" onclick="this.parentNode.parentNode.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="mt-3">
            <a href="/agent/queue" class="text-xs text-blue-600 hover:text-blue-800">
                View Queue <i class="fas fa-arrow-right ml-1"></i>
            </a>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after delay
    setTimeout(() => {
        notification.classList.add('animate-fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
    
    // Play notification sound
    playNotificationSound();
}

// Handle customer message
function handleCustomerMessage(messageData) {
    // Check if we're in the relevant conversation
    const currentConversationId = document.getElementById('conversationId')?.value;
    if (currentConversationId && currentConversationId === messageData.conversation_id) {
        // Add message to chat
        const chatMessages = document.getElementById('agentChatMessages');
        if (chatMessages) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'flex mb-4';
            messageDiv.innerHTML = `
                <div class="flex-shrink-0 mr-3">
                    <div class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <i class="fas fa-user text-gray-600"></i>
                    </div>
                </div>
                <div class="bg-gray-100 p-3 rounded-lg">
                    <p class="text-sm">${messageData.message}</p>
                    <p class="text-xs text-gray-500 mt-1">Just now</p>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    } else {
        // Create notification for message in another conversation
        notifyNewMessage(messageData);
    }
}

// Notify about new message
function notifyNewMessage(messageData) {
    // Create notification
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-4 w-80 border-l-4 border-green-500 animate-slide-in';
    notification.innerHTML = `
        <div class="flex justify-between items-start">
            <div>
                <h4 class="text-sm font-medium text-gray-900">New Message</h4>
                <p class="text-xs text-gray-600 mt-1">${messageData.customer_name || 'Customer'}</p>
                <p class="text-xs text-gray-500 mt-1">${messageData.message.substring(0, 50)}${messageData.message.length > 50 ? '...' : ''}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-500" onclick="this.parentNode.parentNode.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="mt-3">
            <a href="/agent/chat/${messageData.conversation_id}" class="text-xs text-blue-600 hover:text-blue-800">
                View Conversation <i class="fas fa-arrow-right ml-1"></i>
            </a>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after delay
    setTimeout(() => {
        notification.classList.add('animate-fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
    
    // Play notification sound
    playNotificationSound();
}

// Notify about ticket assignment
function notifyTicketAssigned(assignmentData) {
    // Create notification
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-4 w-80 border-l-4 border-purple-500 animate-slide-in';
    notification.innerHTML = `
        <div class="flex justify-between items-start">
            <div>
                <h4 class="text-sm font-medium text-gray-900">Ticket Assigned</h4>
                <p class="text-xs text-gray-600 mt-1">Ticket #${assignmentData.ticket_id}</p>
                <p class="text-xs text-gray-500 mt-1">Assigned to you</p>
            </div>
            <button class="text-gray-400 hover:text-gray-500" onclick="this.parentNode.parentNode.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="mt-3">
            <a href="/agent/ticket/${assignmentData.ticket_id}" class="text-xs text-blue-600 hover:text-blue-800">
                View Ticket <i class="fas fa-arrow-right ml-1"></i>
            </a>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after delay
    setTimeout(() => {
        notification.classList.add('animate-fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
    
    // Play notification sound
    playNotificationSound();
}

// Update agent status in UI
function updateAgentStatusUI(agentId, status) {
    const statusElement = document.querySelector(`[data-agent-id="${agentId}"] .agent-status`);
    if (!statusElement) return;
    
    // Remove all status classes
    statusElement.classList.remove('bg-green-100', 'text-green-800', 'bg-red-100', 'text-red-800', 'bg-yellow-100', 'text-yellow-800', 'bg-gray-100', 'text-gray-800');
    
    // Add appropriate class based on status
    switch (status) {
        case 'available':
            statusElement.classList.add('bg-green-100', 'text-green-800');
            statusElement.innerHTML = '<span class="h-2 w-2 mr-1 bg-green-400 rounded-full"></span> Available';
            break;
        case 'busy':
            statusElement.classList.add('bg-red-100', 'text-red-800');
            statusElement.innerHTML = '<span class="h-2 w-2 mr-1 bg-red-400 rounded-full"></span> Busy';
            break;
        case 'away':
            statusElement.classList.add('bg-yellow-100', 'text-yellow-800');
            statusElement.innerHTML = '<span class="h-2 w-2 mr-1 bg-yellow-400 rounded-full"></span> Away';
            break;
        case 'offline':
            statusElement.classList.add('bg-gray-100', 'text-gray-800');
            statusElement.innerHTML = '<span class="h-2 w-2 mr-1 bg-gray-400 rounded-full"></span> Offline';
            break;
    }
}

// Play notification sound
function playNotificationSound() {
    // Create audio element
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.volume = 0.5;
    audio.play().catch(e => console.log('Audio play failed:', e));
}

// Setup queue management
function setupQueueManagement() {
    const assignButtons = document.querySelectorAll('.assign-ticket-btn');
    assignButtons.forEach(button => {
        button.addEventListener('click', function() {
            const ticketId = this.dataset.ticketId;
            assignTicket(ticketId);
        });
    });
}

// Assign ticket to agent
async function assignTicket(ticketId) {
    try {
        const agentId = document.getElementById('agentId')?.value || 'unknown';
        
        // Show loading state
        const button = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        // In a real implementation, this would make an API call
        console.log(`Assigning ticket ${ticketId} to agent ${agentId}`);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Update UI
        const ticketElement = button.closest('.ticket-item');
        if (ticketElement) {
            ticketElement.classList.add('bg-blue-50', 'border-blue-200');
            button.innerHTML = '<i class="fas fa-check"></i> Assigned';
            button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            button.classList.add('bg-green-600');
            
            // Add assigned badge
            const badgeContainer = ticketElement.querySelector('.ticket-badges');
            if (badgeContainer) {
                const assignedBadge = document.createElement('span');
                assignedBadge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800';
                assignedBadge.innerHTML = 'Assigned to You';
                badgeContainer.appendChild(assignedBadge);
            }
            
            // Add view button
            const actionContainer = button.parentNode;
            const viewButton = document.createElement('a');
            viewButton.href = `/agent/chat/${ticketId}`;
            viewButton.className = 'ml-2 inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500';
            viewButton.innerHTML = 'View <i class="fas fa-arrow-right ml-1"></i>';
            actionContainer.appendChild(viewButton);
        }
        
    } catch (error) {
        console.error('Error assigning ticket:', error);
        alert('Failed to assign ticket. Please try again.');
        
        // Reset button
        const button = document.querySelector(`[data-ticket-id="${ticketId}"]`);
        if (button) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
}

// Setup customer profile view
function setupCustomerProfileView() {
    const customerTabs = document.querySelectorAll('.customer-tab');
    if (customerTabs.length === 0) return;
    
    const tabContents = document.querySelectorAll('.customer-tab-content');
    
    customerTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.dataset.target;
            
            // Update active tab
            customerTabs.forEach(t => t.classList.remove('border-blue-500', 'text-blue-600'));
            this.classList.add('border-blue-500', 'text-blue-600');
            
            // Show target content
            tabContents.forEach(content => {
                if (content.id === target) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
        });
    });
}