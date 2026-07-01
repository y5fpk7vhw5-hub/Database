document.querySelectorAll('input[type="number"]').forEach((input) => {
  input.addEventListener('focus', () => {
    if (input.value === '0') input.select();
  });
});
