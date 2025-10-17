/* scripts.js */

(function () {
    function loadFromLocalStorage(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            return value !== null ? JSON.parse(value) : defaultValue;
        } catch (e) {
            console.warn("Error loading key:", key, e);
            return defaultValue;
        }
    }

    function saveToLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.warn("Error saving key:", key, e);
        }
    }

    function initAutoLocalStorage() {
        const elements = document.querySelectorAll('[data-ls-key]');
        elements.forEach(el => {
            const key = el.dataset.lsKey;

            // --- Load initial value ---
            const saved = loadFromLocalStorage(key);
            if (saved !== null) {
                if (el.type === 'checkbox') {
                    el.checked = !!saved;
                } else {
                    el.value = saved;
                }
            }

            // --- Save on change ---
            const eventType = (el.type === 'checkbox' || el.tagName === 'SELECT') ? 'change' : 'input';
            el.addEventListener(eventType, () => {
                const value = (el.type === 'checkbox') ? el.checked : el.value;
                saveToLocalStorage(key, value);
            });
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAutoLocalStorage);
    } else {
        initAutoLocalStorage();
    }
})();
