// Add this script to capture more browser information
function collectBrowserData() {
    const data = {
        userAgent: navigator.userAgent,
        language: navigator.language,
        cookiesEnabled: navigator.cookieEnabled,
        screenRes: `${window.screen.width}x${window.screen.height}`,
        colorDepth: window.screen.colorDepth,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform: navigator.platform,
        referrer: document.referrer
    };
    
    // Send the data uban ang form
    document.getElementById('browserData').value = JSON.stringify(data);
}

window.addEventListener('load', function() {
    // Add event listener to the form
    const form = document.querySelector('form');
    if (form) {
        // Add hidden field for browser data
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = 'browserData';
        hiddenField.id = 'browserData';
        form.appendChild(hiddenField);
        
        // Collect data when form is submitted
        form.addEventListener('submit', collectBrowserData);
    }
});