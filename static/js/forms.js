document.addEventListener('DOMContentLoaded', () => {
    // Делегирование: работает для динамически добавленных строк
    document.addEventListener('click', (e) => {
        if (e.target.matches('[data-add-row]')) {
            e.preventDefault();
            const table = e.target.closest('form').querySelector('[data-items-table]');
            const tbody = table.querySelector('tbody');
            const row = tbody.rows[0].cloneNode(true);
            row.querySelectorAll('input, select').forEach(el => {
                if (el.tagName === 'INPUT') el.value = el.type === 'number' ? '' : '';
                if (el.tagName === 'SELECT') el.selectedIndex = 0;
            });
            tbody.appendChild(row);
        }
        if (e.target.matches('[data-remove-row]')) {
            e.preventDefault();
            const tbody = e.target.closest('tbody');
            if (tbody.rows.length > 1) e.target.closest('tr').remove();
        }
    });
});