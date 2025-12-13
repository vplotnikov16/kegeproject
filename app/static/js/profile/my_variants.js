document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.js-delete-variant');
    if (!btn) return;

    if (!confirm('Удалить вариант?')) return;

    const url = btn.dataset.url;

    try {
        const resp = await fetch(url, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await resp.json();

        if (!resp.ok || !data.ok) {
            alert(data.message || 'Ошибка удаления');
            return;
        }

        const card = btn.closest('[data-variant-id]');
        card?.remove();

    } catch (err) {
        console.error(err);
        alert('Ошибка сети');
    }
});
