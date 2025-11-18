// static/chatbot.js
// Bursary Application Help Chatbot

class BursaryHelpChatbot {
    constructor() {
        this.chatWindow = document.getElementById('chatbotWindow');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.toggleButton = document.getElementById('chatbotToggle');
        this.notificationBadge = document.getElementById('notificationBadge');
        
        this.isOpen = false;
        this.isTyping = false;
        
        this.knowledgeBase = {
            'application': {
                keywords: ['apply', 'application', 'how to', 'submit', 'process', 'start', 'begin'],
                response: 'To apply for the West Pokot County Bursary:\n\n1. Fill all required fields in the form\n2. Attach required documents (ID, school records, etc.)\n3. Ensure all information is accurate\n4. Submit before the deadline: November 29, 2024\n\nWould you like help with a specific section?',
                quickReplies: ['Documents needed', 'Eligibility', 'Deadline']
            },
            'documents': {
                keywords: ['document', 'attach', 'upload', 'file', 'required', 'papers', 'what to upload'],
                response: 'Required Documents:\n\n📄 Student ID/Birth Certificate\n📋 School Transcript/Report Form\n🆔 Parent/Guardian ID\n🎓 Admission Letter (for college/university)\n📊 Fee Structure\n📸 Passport Photo\n\nEnsure files are PDF, JPG, or PNG format (max 5MB each).',
                quickReplies: ['File format', 'File size', 'Upload issues']
            },
            'eligibility': {
                keywords: ['eligible', 'qualify', 'who can', 'requirements', 'criteria', 'can i apply'],
                response: 'Eligibility Criteria:\n\n✓ Resident of West Pokot County\n✓ Currently enrolled in school/college\n✓ Demonstrated financial need\n✓ Valid student ID/Birth Certificate\n✓ Complete application with all documents\n\nPriority given to orphans, students with disabilities, and those from low-income families.',
                quickReplies: ['Income limits', 'Disability support', 'Orphan benefits']
            },
            'amount': {
                keywords: ['amount', 'how much', 'money', 'fee', 'tuition', 'request', 'payment'],
                response: 'Bursary Amount Guidelines:\n\n• Request should not exceed your tuition fee\n• Based on demonstrated financial need\n• Priority scoring considers:\n  - Family income\n  - Number of siblings in school\n  - Orphan status\n  - Disability status\n\nBe realistic and honest about your needs.',
                quickReplies: ['Calculation', 'Priority factors']
            },
            'deadline': {
                keywords: ['deadline', 'when', 'date', 'close', 'last day', 'time', 'closing'],
                response: 'Important Dates:\n\n📅 Application Deadline: November 29, 2024\n⏰ Submit to: Ward Office\n📧 Processing Time: 2-4 weeks\n\nLate applications may not be considered. Submit as early as possible!',
                quickReplies: ['Ward office location', 'Extension possible?']
            },
            'contact': {
                keywords: ['contact', 'phone', 'email', 'office', 'help', 'support', 'reach', 'call'],
                response: 'Contact Information:\n\n📧 Email: bursary@westpokot.go.ke\n📞 Phone: +254 XXX XXX XXX\n🏢 Office: West Pokot County Bursary Office\n⏰ Hours: Monday-Friday, 8AM-5PM\n\nFor urgent issues, visit the office in person or call during business hours.',
                contact: {
                    email: 'bursary@westpokot.go.ke',
                    phone: '+254 XXX XXX XXX',
                    office: 'West Pokot County Bursary Office',
                    location: 'County Headquarters, Kapenguria',
                    hours: 'Monday - Friday: 8:00 AM - 5:00 PM'
                }
            },
            'errors': {
                keywords: ['error', 'problem', 'not working', 'issue', 'bug', 'failed', 'cant', 'cannot', 'help'],
                response: 'Troubleshooting Common Issues:\n\n1. Form not submitting?\n   → Check all required fields are filled\n   → Verify file sizes are under 5MB\n\n2. Validation errors?\n   → Read error messages carefully\n   → Check date formats (YYYY-MM-DD)\n   → Verify phone number format (+254...)\n\n3. File upload failing?\n   → Use only PDF, JPG, PNG formats\n   → Reduce file size if > 5MB\n\nStill having issues? Contact support.',
                quickReplies: ['File issues', 'Form errors', 'Technical support']
            },
            'status': {
                keywords: ['status', 'check', 'track', 'progress', 'application number', 'result', 'approved', 'rejected'],
                response: 'Checking Application Status:\n\n1. Save your application number (sent via email)\n2. Status updates sent via SMS and email\n3. Processing takes 2-4 weeks\n4. Stages:\n   ① Submitted\n   ② Under Review\n   ③ Chief Verification\n   ④ Committee Review\n   ⑤ Approval/Rejection\n\nFor status inquiries, contact the office with your application number.',
                quickReplies: ['Forgot application number', 'Contact office']
            },
            'format': {
                keywords: ['file format', 'type of file', 'what format', 'pdf', 'jpg', 'png'],
                response: 'Accepted File Formats:\n\n✓ PDF (.pdf) - Recommended for documents\n✓ JPG/JPEG (.jpg, .jpeg) - For photos\n✓ PNG (.png) - For scanned images\n\n❌ NOT Accepted:\n• Word documents (.doc, .docx)\n• Excel files\n• Videos or audio files\n\nConvert documents to PDF before uploading.',
                quickReplies: ['How to convert to PDF', 'File size limit']
            },
            'size': {
                keywords: ['file size', 'too large', 'too big', 'compress', 'reduce'],
                response: 'File Size Requirements:\n\n📏 Maximum: 5MB per file\n\nIf your file is too large:\n1. Use online PDF compressors (e.g., SmallPDF)\n2. Reduce image quality\n3. Convert to black & white\n4. Split multi-page documents\n\nTip: Most phone cameras produce files under 3MB.',
                quickReplies: ['Compress PDF online', 'Reduce image size']
            }
        };
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.toggleButton.addEventListener('click', () => this.toggle());
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Initial greeting
        this.addBotMessage(
            'Hello! 👋 I\'m here to help with your West Pokot County Bursary application.\n\nHow can I assist you today?',
            ['Application process', 'Required documents', 'Eligibility', 'Contact support']
        );
        
        // Show notification after 5 seconds if not opened
        setTimeout(() => {
            if (!this.isOpen) {
                this.notificationBadge.style.display = 'flex';
            }
        }, 5000);
    }
    
    toggle() {
        this.isOpen = !this.isOpen;
        this.chatWindow.classList.toggle('active');
        this.toggleButton.classList.toggle('active');
        this.toggleButton.textContent = this.isOpen ? '✕' : '💬';
        this.notificationBadge.style.display = 'none';
        
        if (this.isOpen) {
            this.chatInput.focus();
            this.scrollToBottom();
        }
    }
    
    sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isTyping) return;
        
        this.addUserMessage(message);
        this.chatInput.value = '';
        
        // Process message
        setTimeout(() => this.processMessage(message), 500);
    }
    
    processMessage(message) {
        const lowerMessage = message.toLowerCase();
        let matched = false;
        
        // Check knowledge base
        for (const [key, data] of Object.entries(this.knowledgeBase)) {
            if (data.keywords.some(keyword => lowerMessage.includes(keyword))) {
                this.showTypingIndicator();
                setTimeout(() => {
                    this.hideTypingIndicator();
                    this.addBotMessage(data.response, data.quickReplies);
                    
                    // Show contact card if contact info requested
                    if (data.contact) {
                        this.addContactCard(data.contact);
                    }
                }, 1500);
                matched = true;
                break;
            }
        }
        
        // Default response if no match
        if (!matched) {
            this.showTypingIndicator();
            setTimeout(() => {
                this.hideTypingIndicator();
                this.addBotMessage(
                    'I\'m not sure about that specific question. Here are some topics I can help with:',
                    ['Application process', 'Documents', 'Eligibility', 'Contact support', 'Deadlines']
                );
            }, 1000);
        }
    }
    
    addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(text)}</div>
            <div class="message-avatar">👤</div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addBotMessage(text, quickReplies = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        
        let quickRepliesHtml = '';
        if (quickReplies && quickReplies.length > 0) {
            quickRepliesHtml = `
                <div class="quick-replies">
                    ${quickReplies.map(reply => 
                        `<button class="quick-reply-btn" onclick="chatbot.handleQuickReply('${reply}')">${reply}</button>`
                    ).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div>
                <div class="message-content">${this.formatText(text)}</div>
                ${quickRepliesHtml}
            </div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addContactCard(contact) {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'message bot';
        cardDiv.innerHTML = `
            <div class="message-avatar">📞</div>
            <div class="message-content">
                <div class="contact-card">
                    <h4>Contact Details</h4>
                    <div class="contact-item">
                        <strong>📧 Email:</strong>
                        <a href="mailto:${contact.email}">${contact.email}</a>
                    </div>
                    <div class="contact-item">
                        <strong>📞 Phone:</strong>
                        <a href="tel:${contact.phone}">${contact.phone}</a>
                    </div>
                    <div class="contact-item">
                        <strong>🏢 Office:</strong>
                        <span>${contact.office}</span>
                    </div>
                    <div class="contact-item">
                        <strong>📍 Location:</strong>
                        <span>${contact.location}</span>
                    </div>
                    <div class="contact-item">
                        <strong>⏰ Hours:</strong>
                        <span>${contact.hours}</span>
                    </div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(cardDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    }
    
    handleQuickReply(reply) {
        this.chatInput.value = reply;
        this.sendMessage();
    }
    
    formatText(text) {
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
}
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatbot = new BursaryHelpChatbot();
});