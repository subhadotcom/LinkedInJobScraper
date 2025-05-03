/**
 * LinkedIn Job Scraper - Main JavaScript file
 */

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Add confirmation for actions that need it
    document.querySelectorAll('.needs-confirmation').forEach(function(element) {
        element.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to perform this action?')) {
                event.preventDefault();
            }
        });
    });
});