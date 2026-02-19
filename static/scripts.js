document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            // Validación ejemplo: Asegura campos requeridos
            const required = form.querySelectorAll('[required]');
            let valid = true;
            required.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            if (!valid) {
                e.preventDefault();
                alert('Por favor, llena todos los campos requeridos.');
            }
        });
    });
});