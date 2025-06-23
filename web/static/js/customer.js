// Customer Interface JavaScript
import { supabase, showMessage } from './auth.js';

document.addEventListener('DOMContentLoaded', function() {
    initializeChatInterface();
    setupKnowledgeSearch();
    initializeTicketSystem();
    setupFeedbackForm();
});

// Initialize chat interface
function initializeChatInterface() {
    const chatForm = document.getElementById('chatForm');
    if (!chatForm) return;

    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const customerId = document.getElementById('customerId')?.value || 'guest';
    const conversationIdInput = document.getElementById('conversationId');
    
    // Function to add message to chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex mb-4' + (isUser ? ' justify-end' : '');
        
        if (isUser) {
            messageDiv.innerHTML = `
                <div class="message-bubble user-message p-3">
                    <p class="text-sm">${message}</p>
                    <p class="text-xs text-gray-500 mt-1">Just now</p>
                </div>
                <div class="flex-shrink-0 ml-3">
                    <div class="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                        <i class="fas fa-user text-white"></i>
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="flex-shrink-0 mr-3">
                    <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <i class="fas fa-robot text-blue-600"></i>
                    </div>
                </div>
                <div class="message-bubble agent-message p-3">
                    <p class="text-sm">${message}</p>
                    <p class="text-xs text-gray-500 mt-1">Just now</p>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex mb-4 typing-container';
        typingDiv.innerHTML = `
            <div class="flex-shrink-0 mr-3">
                <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <i class="fas fa-robot text-blue-600"></i>
                </div>
            </div>
            <div class="message-bubble agent-message p-3 typing-indicator">
                <p class="text-sm">
                    <span>.</span><span>.</span><span>.</span>
                </p>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return typingDiv;
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-container');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Function to send message to server
    async function sendMessage(message) {
        try {
            // Get auth token if user is logged in
            let headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            };
            
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                headers['Authorization'] = `Bearer ${session.access_token}`;
                headers['X-Supabase-Auth'] = session.access_token;
            }
            
            // Prepare form data
            const formData = new URLSearchParams();
            formData.append('customer_id', customerId);
            formData.append('message', message);
            
            if (conversationIdInput.value) {
                formData.append('conversation_id', conversationIdInput.value);
            }
            
            const typingIndicator = showTypingIndicator();
            
            // Make API call to send message
            const apiResponse = await fetch('/customer/chat/message', {
                method: 'POST',
                headers: headers,
                body: formData,
            });

            removeTypingIndicator();

            if (!apiResponse.ok) {
                // Handle server errors (e.g., 500 Internal Server Error)
                const errorData = await apiResponse.json();
                throw new Error(errorData.error || 'The server returned an error.');
            }

            const responseData = await apiResponse.json();
            
            if (responseData.status === 'success') {
                // Save the conversation ID returned by the server
                conversationIdInput.value = responseData.conversation_id;
                
                // Add agent response from the server to the chat
                addMessage(responseData.response.text, false);
            } else {
                // Handle logical errors returned by the server
                throw new Error(responseData.error || 'An unknown error occurred.');
            }
            
        } catch (error) {
            removeTypingIndicator();
            addMessage('Sorry, there was an error connecting to our servers. Please try again later.', false);
            console.error('Error:', error);
        }
    }
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input
        messageInput.value = '';
        
        // Send message to server
        sendMessage(message);
    });
    
    // End chat button
    document.getElementById('endChatBtn')?.addEventListener('click', function() {
        if (confirm('Are you sure you want to end this chat?')) {
            addMessage('Chat ended. If you need further assistance, you can start a new chat or create a support ticket.', false);
            chatForm.style.display = 'none';
            
            // Add feedback request
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'mt-4 p-4 bg-blue-50 rounded-lg';
            feedbackDiv.innerHTML = `
                <p class="text-sm font-medium text-gray-900 mb-2">How would you rate your experience?</p>
                <div class="flex space-x-2 mb-3">
                    <button class="feedback-btn px-3 py-1 border border-gray-300 rounded-md hover:bg-blue-100" data-rating="1">1</button>
                    <button class="feedback-btn px-3 py-1 border border-gray-300 rounded-md hover:bg-blue-100" data-rating="2">2</button>
                    <button class="feedback-btn px-3 py-1 border border-gray-300 rounded-md hover:bg-blue-100" data-rating="3">3</button>
                    <button class="feedback-btn px-3 py-1 border border-gray-300 rounded-md hover:bg-blue-100" data-rating="4">4</button>
                    <button class="feedback-btn px-3 py-1 border border-gray-300 rounded-md hover:bg-blue-100" data-rating="5">5</button>
                </div>
                <p class="text-xs text-gray-500">Thank you for your feedback!</p>
            `;
            
            document.querySelector('.chat-messages').appendChild(feedbackDiv);
            
            // Add event listeners to feedback buttons
            feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const rating = this.getAttribute('data-rating');
                    // Here you would send the rating to your server
                    alert(`Thank you for your feedback! You rated this conversation ${rating}/5.`);
                    
                    // Highlight selected button
                    feedbackDiv.querySelectorAll('.feedback-btn').forEach(b => {
                        b.classList.remove('bg-blue-500', 'text-white');
                    });
                    this.classList.add('bg-blue-500', 'text-white');
                });
            });
        }
    });
}

// Setup knowledge base search
function setupKnowledgeSearch() {
    const searchForm = document.getElementById('knowledgeSearchForm');
    if (!searchForm) return;
    
    const searchInput = document.getElementById('knowledgeSearchInput');
    const searchResults = document.getElementById('knowledgeSearchResults');
    
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = searchInput.value.trim();
        if (!query) return;
        
        // Show loading state
        searchResults.innerHTML = `
            <div class="p-4 text-center">
                <i class="fas fa-spinner fa-spin text-blue-600 text-2xl"></i>
                <p class="mt-2 text-gray-600">Searching...</p>
            </div>
        `;
        
        // Simulate search delay
        setTimeout(() => {
            // Mock search results
            const results = getMockSearchResults(query);
            
            if (results.length === 0) {
                searchResults.innerHTML = `
                    <div class="p-4 text-center">
                        <i class="fas fa-search text-gray-400 text-2xl"></i>
                        <p class="mt-2 text-gray-600">No results found for "${query}"</p>
                    </div>
                `;
            } else {
                searchResults.innerHTML = `
                    <div class="p-4">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">Search Results for "${query}"</h3>
                        <div class="space-y-4">
                            ${results.map(result => `
                                <div class="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                                    <h4 class="text-md font-semibold text-gray-900 mb-1">${result.title}</h4>
                                    <p class="text-sm text-gray-600 mb-2">${result.excerpt}</p>
                                    <a href="${result.url}" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                        Read More <i class="fas fa-arrow-right ml-1"></i>
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        }, 1000);
    });
    
    // Mock search results for demo
    function getMockSearchResults(query) {
        const allResults = [
            {
                title: "How to Reset Your Password",
                excerpt: "Step-by-step guide to reset your account password and regain access to your account.",
                url: "/customer/knowledge/account"
            },
            {
                title: "API Integration Guide",
                excerpt: "Complete guide to integrating with our API, including authentication and endpoints.",
                url: "/customer/knowledge/technical"
            },
            {
                title: "Billing and Payment FAQ",
                excerpt: "Answers to common questions about billing cycles, payment methods, and invoices.",
                url: "/customer/knowledge/billing"
            },
            {
                title: "Troubleshooting Common Issues",
                excerpt: "Solutions to the most common technical problems and error messages.",
                url: "/customer/knowledge/technical"
            }
        ];
        
        // Filter results based on query
        const queryLower = query.toLowerCase();
        return allResults.filter(result => 
            result.title.toLowerCase().includes(queryLower) || 
            result.excerpt.toLowerCase().includes(queryLower)
        );
    }
}

// Initialize ticket system
function initializeTicketSystem() {
    const ticketForm = document.getElementById('ticketForm');
    if (!ticketForm) return;
    
    ticketForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const subject = document.getElementById('ticketSubject').value;
        const category = document.getElementById('ticketCategory').value;
        const description = document.getElementById('ticketDescription').value;
        
        if (!subject || !category || !description) {
            alert('Please fill out all required fields');
            return;
        }
        
        // Show loading state
        const submitButton = ticketForm.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Submitting...';
        submitButton.disabled = true;
        
        try {
            // Get auth token
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                throw new Error('You must be logged in to create a ticket');
            }
            
            // In a real implementation, this would make an API call
            // For now, we'll simulate a successful ticket creation
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Reset form
            ticketForm.reset();
            
            // Show success message
            const successMessage = document.createElement('div');
            successMessage.className = 'bg-green-50 border border-green-200 text-green-800 rounded-lg p-4 mb-4';
            successMessage.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-check-circle text-green-500"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium">Ticket created successfully!</p>
                        <p class="text-xs mt-1">Ticket #TICK-${Math.floor(1000 + Math.random() * 9000)}</p>
                    </div>
                </div>
            `;
            
            ticketForm.parentNode.insertBefore(successMessage, ticketForm);
            
            // Reset button
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
            
            // Remove success message after delay
            setTimeout(() => {
                successMessage.remove();
            }, 5000);
            
        } catch (error) {
            console.error('Error creating ticket:', error);
            
            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mb-4';
            errorMessage.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-circle text-red-500"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium">Error creating ticket</p>
                        <p class="text-xs mt-1">${error.message}</p>
                    </div>
                </div>
            `;
            
            ticketForm.parentNode.insertBefore(errorMessage, ticketForm);
            
            // Reset button
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
            
            // Remove error message after delay
            setTimeout(() => {
                errorMessage.remove();
            }, 5000);
        }
    });
}

// Setup feedback form
function setupFeedbackForm() {
    const feedbackForm = document.getElementById('feedbackForm');
    if (!feedbackForm) return;
    
    // Setup star rating
    const ratingContainer = document.getElementById('ratingContainer');
    const ratingInput = document.getElementById('ratingInput');
    
    if (ratingContainer && ratingInput) {
        // Create star elements
        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('span');
            star.className = 'text-gray-300 text-2xl cursor-pointer hover:text-yellow-500';
            star.innerHTML = '<i class="fas fa-star"></i>';
            star.dataset.rating = i;
            
            star.addEventListener('click', function() {
                const rating = parseInt(this.dataset.rating);
                ratingInput.value = rating;
                
                // Update star colors
                const stars = ratingContainer.querySelectorAll('span');
                stars.forEach((s, index) => {
                    if (index < rating) {
                        s.className = 'text-yellow-500 text-2xl cursor-pointer';
                    } else {
                        s.className = 'text-gray-300 text-2xl cursor-pointer hover:text-yellow-500';
                    }
                });
            });
            
            ratingContainer.appendChild(star);
        }
    }
    
    // Handle form submission
    feedbackForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const rating = ratingInput.value;
        const category = document.getElementById('feedbackCategory').value;
        const message = document.getElementById('feedbackMessage').value;
        
        if (!rating || !category || !message) {
            alert('Please fill out all required fields');
            return;
        }
        
        // Show loading state
        const submitButton = feedbackForm.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Submitting...';
        submitButton.disabled = true;
        
        try {
            // Get auth token if available
            const { data: { session } } = await supabase.auth.getSession();
            const customerId = session ? session.user.id : 'guest';
            
            // In a real implementation, this would make an API call
            // For now, we'll simulate a successful submission
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Reset form
            feedbackForm.reset();
            
            // Reset star rating
            const stars = ratingContainer.querySelectorAll('span');
            stars.forEach(s => {
                s.className = 'text-gray-300 text-2xl cursor-pointer hover:text-yellow-500';
            });
            
            // Show thank you message
            const thankYouMessage = document.createElement('div');
            thankYouMessage.className = 'bg-green-50 border border-green-200 text-green-800 rounded-lg p-4 mb-4';
            thankYouMessage.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-heart text-green-500"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium">Thank you for your feedback!</p>
                        <p class="text-xs mt-1">We appreciate your input and will use it to improve our service.</p>
                    </div>
                </div>
            `;
            
            feedbackForm.parentNode.insertBefore(thankYouMessage, feedbackForm);
            
            // Reset button
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
            
            // Remove thank you message after delay
            setTimeout(() => {
                thankYouMessage.remove();
            }, 5000);
            
        } catch (error) {
            console.error('Error submitting feedback:', error);
            
            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mb-4';
            errorMessage.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-circle text-red-500"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium">Error submitting feedback</p>
                        <p class="text-xs mt-1">${error.message}</p>
                    </div>
                </div>
            `;
            
            feedbackForm.parentNode.insertBefore(errorMessage, feedbackForm);
            
            // Reset button
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
            
            // Remove error message after delay
            setTimeout(() => {
                errorMessage.remove();
            }, 5000);
        }
    });
}