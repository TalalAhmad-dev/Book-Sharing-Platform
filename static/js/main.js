document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 600);
        }, 4000);
    });
});
