/**
 * Admin panel JavaScript functionality
 */

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle confirmation dialogs
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const message = form.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // Get current year for footer
    const currentYear = new Date().getFullYear();
    const yearElements = document.querySelectorAll('.current-year');
    yearElements.forEach(function(el) {
        el.textContent = currentYear;
    });
    
    // Product image preview on add/edit forms
    const imageUrlInput = document.getElementById('image_url');
    if (imageUrlInput) {
        imageUrlInput.addEventListener('change', function() {
            // Check if there's an existing preview
            let previewContainer = document.getElementById('image-preview');
            
            if (!previewContainer) {
                // Create preview container if it doesn't exist
                previewContainer = document.createElement('div');
                previewContainer.id = 'image-preview';
                previewContainer.className = 'mt-3 text-center';
                imageUrlInput.parentNode.appendChild(previewContainer);
            }
            
            // Clear existing preview
            previewContainer.innerHTML = '';
            
            if (this.value) {
                const img = document.createElement('img');
                img.src = this.value;
                img.alt = 'Product image preview';
                img.className = 'img-fluid border rounded';
                img.style.maxHeight = '200px';
                
                // Handle load errors
                img.onerror = function() {
                    previewContainer.innerHTML = '<div class="alert alert-warning">Image could not be loaded</div>';
                };
                
                previewContainer.appendChild(img);
            }
        });
        
        // Trigger change event to show preview for existing images
        if (imageUrlInput.value) {
            const event = new Event('change');
            imageUrlInput.dispatchEvent(event);
        }
    }
});
