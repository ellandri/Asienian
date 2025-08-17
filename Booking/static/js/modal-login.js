// Script pour ouvrir automatiquement le modal de connexion si l'utilisateur n'est pas authentifié
// Nécessite Bootstrap 5

document.addEventListener('DOMContentLoaded', function () {
    // Sécurité : ne jamais afficher le modal sur /accounts/login/
    if (window.location.pathname === '/accounts/login/') {
        window.location.replace('/');
        return;
    }
    if (typeof window.USER_AUTHENTICATED !== 'undefined' && !window.USER_AUTHENTICATED) {
        // Empêche le scroll et interactions
        document.body.classList.add('modal-open');
        // Affiche le backdrop
        let backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
        // Ouvre le modal
        let loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
    }
});

// Soumission AJAX du formulaire de connexion dans le modal
const loginForm = document.querySelector('#loginModal form');
if (loginForm) {
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(loginForm);
        fetch(loginForm.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Redirige vers l'URL fournie (ex: index-tour.html)
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.reload();
                }
            } else {
                // Affiche les erreurs dans le formulaire
                const errorDiv = loginForm.querySelector('.alert-danger') || document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.innerHTML = '';
                if (data.errors) {
                    for (const err of data.errors) {
                        errorDiv.innerHTML += `<div>${err}</div>`;
                    }
                }
                if (!loginForm.querySelector('.alert-danger')) {
                    loginForm.prepend(errorDiv);
                }
                // Reste sur la page, modal toujours ouvert
            }
        })
        .catch(() => {
            alert('Erreur réseau.');
        });
    });
}
