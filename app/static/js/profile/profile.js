document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.getElementById('avatar-file-input');
  const avatarImg = document.getElementById('profile-avatar-img');
  const deleteBtn = document.getElementById('avatar-delete-btn');

  if (fileInput && avatarImg) {
    fileInput.addEventListener('change', () => {
      const f = fileInput.files && fileInput.files[0];
      if (!f) return;
      if (!f.type.startsWith('image/')) {
        alert('Пожалуйста, выберите изображение.');
        fileInput.value = '';
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        avatarImg.src = e.target.result;
      };
      reader.readAsDataURL(f);
    });
  }

  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (e) => {
      if (!confirm('Удалить аватар? Это действие необратимо.')) return;
      const url = deleteBtn.dataset.action;
      try {
        const res = await fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' }});
        if (res.ok) {
          location.reload();
        } else {
          const js = await res.json().catch(()=>null);
          alert((js && js.message) ? js.message : 'Ошибка при удалении аватара');
        }
      } catch (err) {
        alert('Ошибка: ' + err);
      }
    });
  }
});
