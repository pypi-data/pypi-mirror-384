function back_button() {
    const form = document.getElementById('form');
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'back_button';
    input.value = '1';
    form.appendChild(input);
    form.noValidate = true;
    form.submit();
}
