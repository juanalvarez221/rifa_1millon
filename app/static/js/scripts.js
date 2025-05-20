document.addEventListener('DOMContentLoaded', () => {
    // Mostrar alertas de forma temporal
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            alert.classList.add('fade');
        }, 5000);
    });

    // Temporizador para reservas
    const temporizadorElement = document.getElementById('temporizador');
    if (temporizadorElement) {
        const expiraEn = new Date(temporizadorElement.dataset.expira).getTime();
        const actualizarTemporizador = () => {
            const ahora = new Date().getTime();
            const distancia = expiraEn - ahora;
            if (distancia <= 0) {
                temporizadorElement.innerHTML = '¡La reserva ha expirado! 😔';
                document.querySelector('form').style.display = 'none';
                return;
            }
            const minutos = Math.floor((distancia % (1000 * 60 * 60)) / (1000 * 60));
            const segundos = Math.floor((distancia % (1000 * 60)) / 1000);
            temporizadorElement.innerHTML = `Tiempo restante: ${minutos}m ${segundos}s`;
        };
        actualizarTemporizador();
        setInterval(actualizarTemporizador, 1000);
    }
});