/**
 * Aalam Synak - Main JavaScript
 * Common functionality and utilities
 */

(function () {
    'use strict';

    // Sidebar toggle for mobile
    function initSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const toggle = document.querySelector('.sidebar-toggle');
        const overlay = document.querySelector('.sidebar-overlay');

        if (toggle && sidebar) {
            toggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
                if (overlay) overlay.classList.toggle('open');
            });

            if (overlay) {
                overlay.addEventListener('click', () => {
                    sidebar.classList.remove('open');
                    overlay.classList.remove('open');
                });
            }
        }
    }

    // Language selector dropdown
    function initLanguageSelector() {
        const selectors = document.querySelectorAll('.lang-selector');

        selectors.forEach(selector => {
            const btn = selector.querySelector('.lang-btn');

            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    selector.classList.toggle('open');
                });
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            selectors.forEach(selector => selector.classList.remove('open'));
        });
    }

    // Alert auto-dismiss
    function initAlerts() {
        const alerts = document.querySelectorAll('.alert[data-dismiss]');

        alerts.forEach(alert => {
            const dismissTime = parseInt(alert.dataset.dismiss) || 5000;
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, dismissTime);
        });
    }

    // Form validation enhancement
    function initForms() {
        const forms = document.querySelectorAll('form[data-validate]');

        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.classList.add('error');
                    } else {
                        field.classList.remove('error');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                }
            });
        });
    }

    // Confirm dialogs
    function initConfirmDialogs() {
        document.querySelectorAll('[data-confirm]').forEach(element => {
            element.addEventListener('click', (e) => {
                const message = element.dataset.confirm || 'Are you sure?';
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    }

    // Responsive Tables Automation
    function initResponsiveTables() {
        const tables = document.querySelectorAll('table.table, table.data-table, table.reg-table, table.split-table');
        tables.forEach(table => {
            if (table.classList.contains('no-responsive')) return;
            
            // Wrap in overflow container natively
            if (!table.parentElement.classList.contains('table-container')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-container';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
            
            // Embed data labels for CSS extraction
            const thead = table.querySelector('thead');
            if (thead) {
                const headers = Array.from(thead.querySelectorAll('th')).map(th => th.innerText.trim());
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    cells.forEach((cell, index) => {
                        if (headers[index]) {
                            cell.setAttribute('data-label', headers[index]);
                        }
                    });
                });
                table.classList.add('mobile-cards');
            }
        });
    }

    // Initialize all components
    function init() {
        initSidebar();
        initLanguageSelector();
        initAlerts();
        initForms();
        initConfirmDialogs();
        initResponsiveTables();
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
