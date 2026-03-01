// ==========================================
// Validaciones en tiempo real para el formulario de registro
// Con soporte para reCAPTCHA
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registroForm');
    if (!form) return;
    
    // Obtener elementos del formulario
    const nombreInput = document.getElementById('nombre');
    const correoInput = document.getElementById('correo');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const terminosCheckbox = document.getElementById('terminos');
    const submitBtn = document.getElementById('submitBtn');
    const togglePasswordBtn = document.getElementById('togglePassword');
    
    // Obtener elementos de feedback
    const nombreFeedback = document.getElementById('nombreFeedback');
    const correoFeedback = document.getElementById('correoFeedback');
    const passwordFeedback = document.getElementById('passwordFeedback');
    const confirmPasswordFeedback = document.getElementById('confirmPasswordFeedback');
    const terminosFeedback = document.getElementById('terminosFeedback');
    const passwordStrength = document.getElementById('passwordStrength');
    
    // Estado de validación (expuesto globalmente para reCAPTCHA)
    window.validacionesEstado = {
        nombre: false,
        correo: false,
        password: false,
        confirmPassword: false,
        terminos: false
    };
    
    // Evento personalizado para notificar cambios
    function dispatchValidacionActualizada() {
        const event = new CustomEvent('validacionActualizada');
        document.dispatchEvent(event);
    }
    
    // ==========================================
    // Validación del Nombre
    // ==========================================
    nombreInput.addEventListener('input', function() {
        const valor = this.value;
        
        // Solo letras, sin espacios ni números
        const regex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$/;
        
        if (valor === '') {
            mostrarFeedback(nombreFeedback, '', 'hide');
            window.validacionesEstado.nombre = false;
            nombreInput.classList.remove('valid', 'invalid');
        } else if (!regex.test(valor)) {
            if (/\s/.test(valor)) {
                mostrarFeedback(nombreFeedback, '✕ No se permiten espacios', 'error');
            } else if (/\d/.test(valor)) {
                mostrarFeedback(nombreFeedback, '✕ No se permiten números', 'error');
            } else {
                mostrarFeedback(nombreFeedback, '✕ Solo se permiten letras', 'error');
            }
            window.validacionesEstado.nombre = false;
            nombreInput.classList.remove('valid');
            nombreInput.classList.add('invalid');
        } else if (valor.length < 3) {
            mostrarFeedback(nombreFeedback, '✕ Mínimo 3 caracteres', 'error');
            window.validacionesEstado.nombre = false;
            nombreInput.classList.remove('valid');
            nombreInput.classList.add('invalid');
        } else {
            mostrarFeedback(nombreFeedback, '✓ Nombre válido', 'success');
            window.validacionesEstado.nombre = true;
            nombreInput.classList.remove('invalid');
            nombreInput.classList.add('valid');
        }
        
        dispatchValidacionActualizada();
    });
    
    // ==========================================
// Validación del Correo
// ==========================================
correoInput.addEventListener('input', function() {
    const valor = this.value;
    
    // Debe contener @ y después del último punto al menos 2 caracteres
    const tieneArroba = valor.includes('@');
    
    // Verificar que después del último punto haya al menos 2 caracteres
    const ultimoPuntoIndex = valor.lastIndexOf('.');
    const despuesDelPunto = ultimoPuntoIndex !== -1 ? valor.substring(ultimoPuntoIndex + 1) : '';
    const dominioValido = despuesDelPunto.length >= 2;
    
    if (valor === '') {
        mostrarFeedback(correoFeedback, '', 'hide');
        window.validacionesEstado.correo = false;
        correoInput.classList.remove('valid', 'invalid');
    } else if (!tieneArroba && !dominioValido) {
        mostrarFeedback(correoFeedback, '✕ Debe contener @ y tener dominio válido (ej: .com, .pe, .mx)', 'error');
        window.validacionesEstado.correo = false;
        correoInput.classList.remove('valid');
        correoInput.classList.add('invalid');
    } else if (!tieneArroba) {
        mostrarFeedback(correoFeedback, '✕ Debe contener @', 'error');
        window.validacionesEstado.correo = false;
        correoInput.classList.remove('valid');
        correoInput.classList.add('invalid');
    } else if (!dominioValido) {
        mostrarFeedback(correoFeedback, '✕ Dominio inválido. Ejemplos: .com, .pe, .mx (mínimo 2 letras después del punto)', 'error');
        window.validacionesEstado.correo = false;
        correoInput.classList.remove('valid');
        correoInput.classList.add('invalid');
    } else {
        // Validación adicional de formato completo
        // Acepta: usuario@dominio.com, usuario@sub.dominio.com, usuario@dominio.pe
        const regexEmail = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?$/;
        if (!regexEmail.test(valor)) {
            mostrarFeedback(correoFeedback, '✕ Formato de correo inválido', 'error');
            window.validacionesEstado.correo = false;
            correoInput.classList.remove('valid');
            correoInput.classList.add('invalid');
        } else {
            mostrarFeedback(correoFeedback, '✓ Correo válido', 'success');
            window.validacionesEstado.correo = true;
            correoInput.classList.remove('invalid');
            correoInput.classList.add('valid');
        }
    }
    
    dispatchValidacionActualizada();
});
    
    // ==========================================
    // Validación de Contraseña
    // ==========================================
    passwordInput.addEventListener('input', function() {
        const valor = this.value;
        
        if (valor === '') {
            mostrarFeedback(passwordFeedback, '', 'hide');
            window.validacionesEstado.password = false;
            passwordInput.classList.remove('valid', 'invalid');
            passwordStrength.classList.remove('show');
        } else {
            passwordStrength.classList.add('show');
            
            // Criterios de validación
            const tieneMayuscula = /[A-Z]/.test(valor);
            const tieneMinuscula = /[a-z]/.test(valor);
            const tieneNumero = /\d/.test(valor);
            const longitudMinima = valor.length >= 8;
            
            let errores = [];
            if (!longitudMinima) errores.push('mínimo 8 caracteres');
            if (!tieneMayuscula) errores.push('una mayúscula');
            if (!tieneMinuscula) errores.push('una minúscula');
            if (!tieneNumero) errores.push('un número');
            
            // Actualizar indicador de fortaleza
            actualizarFortalezaPassword(valor);
            
            if (errores.length > 0) {
                mostrarFeedback(passwordFeedback, `✕ Falta: ${errores.join(', ')}`, 'error');
                window.validacionesEstado.password = false;
                passwordInput.classList.remove('valid');
                passwordInput.classList.add('invalid');
            } else {
                mostrarFeedback(passwordFeedback, '✓ Contraseña segura', 'success');
                window.validacionesEstado.password = true;
                passwordInput.classList.remove('invalid');
                passwordInput.classList.add('valid');
            }
        }
        
        // Re-validar confirmación si ya tiene valor
        if (confirmPasswordInput.value) {
            validarConfirmPassword();
        }
        
        dispatchValidacionActualizada();
    });
    
    // ==========================================
    // Función para actualizar fortaleza de contraseña
    // ==========================================
    function actualizarFortalezaPassword(password) {
        const strengthBars = passwordStrength.querySelectorAll('.strength-bar');
        const strengthText = passwordStrength.querySelector('.strength-text');
        
        let fuerza = 0;
        
        if (password.length >= 8) fuerza++;
        if (/[A-Z]/.test(password)) fuerza++;
        if (/[a-z]/.test(password)) fuerza++;
        if (/\d/.test(password)) fuerza++;
        
        // Remover clase active de todas las barras
        strengthBars.forEach(bar => bar.classList.remove('active'));
        
        // Activar barras según la fuerza
        for (let i = 0; i < fuerza; i++) {
            strengthBars[i].classList.add('active');
        }
        
        // Actualizar texto
        const textos = ['Muy débil', 'Débil', 'Media', 'Fuerte', 'Muy fuerte'];
        strengthText.textContent = `Fortaleza: ${textos[fuerza] || 'Muy débil'}`;
    }
    
    // ==========================================
    // Validación de Confirmar Contraseña
    // ==========================================
    confirmPasswordInput.addEventListener('input', validarConfirmPassword);
    
    function validarConfirmPassword() {
        const valor = confirmPasswordInput.value;
        const passwordValor = passwordInput.value;
        
        if (valor === '') {
            mostrarFeedback(confirmPasswordFeedback, '', 'hide');
            window.validacionesEstado.confirmPassword = false;
            confirmPasswordInput.classList.remove('valid', 'invalid');
        } else if (valor !== passwordValor) {
            mostrarFeedback(confirmPasswordFeedback, '✕ Las contraseñas no coinciden', 'error');
            window.validacionesEstado.confirmPassword = false;
            confirmPasswordInput.classList.remove('valid');
            confirmPasswordInput.classList.add('invalid');
        } else {
            mostrarFeedback(confirmPasswordFeedback, '✓ Las contraseñas coinciden', 'success');
            window.validacionesEstado.confirmPassword = true;
            confirmPasswordInput.classList.remove('invalid');
            confirmPasswordInput.classList.add('valid');
        }
        
        dispatchValidacionActualizada();
    }
    
    // ==========================================
    // Validación de Términos y Condiciones
    // ==========================================
    terminosCheckbox.addEventListener('change', function() {
        if (this.checked) {
            window.validacionesEstado.terminos = true;
            mostrarFeedback(terminosFeedback, '', 'hide');
        } else {
            window.validacionesEstado.terminos = false;
        }
        dispatchValidacionActualizada();
    });
    
    // ==========================================
    // Función para mostrar feedback
    // ==========================================
    function mostrarFeedback(elemento, mensaje, tipo) {
        elemento.textContent = mensaje;
        elemento.classList.remove('show', 'success', 'error', 'hide');
        
        if (tipo !== 'hide') {
            elemento.classList.add('show', tipo);
        }
    }
    
    // ==========================================
    // Toggle de visibilidad de contraseña
    // ==========================================
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', function() {
            const eyeIcon = this.querySelector('.eye-icon');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                eyeIcon.textContent = '👁️‍🗨️';
            } else {
                passwordInput.type = 'password';
                eyeIcon.textContent = '👁';
            }
        });
    }
    
    // ==========================================
    // Validación al enviar el formulario
    // ==========================================
    form.addEventListener('submit', function(e) {
        const todasValidas = Object.values(window.validacionesEstado).every(v => v === true);
        
        // Verificar reCAPTCHA
        const recaptchaResponse = grecaptcha.getResponse();
        if (!recaptchaResponse) {
            e.preventDefault();
            alert('Por favor, completa la verificación de reCAPTCHA');
            return false;
        }
        
        if (!todasValidas) {
            e.preventDefault();
            
            // Mostrar errores en los campos sin validar
            if (!window.validacionesEstado.nombre && nombreInput.value) {
                nombreInput.focus();
            } else if (!window.validacionesEstado.correo && correoInput.value) {
                correoInput.focus();
            } else if (!window.validacionesEstado.password && passwordInput.value) {
                passwordInput.focus();
            } else if (!window.validacionesEstado.confirmPassword && confirmPasswordInput.value) {
                confirmPasswordInput.focus();
            } else if (!window.validacionesEstado.terminos) {
                mostrarFeedback(terminosFeedback, '✕ Debes aceptar los términos y condiciones', 'error');
            }
            
            return false;
        }
    });
    
    // ==========================================
    // Animación de entrada para los campos
    // ==========================================
    const formGroups = document.querySelectorAll('.form-group');
    formGroups.forEach((group, index) => {
        group.style.opacity = '0';
        group.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            group.style.transition = 'all 0.4s ease';
            group.style.opacity = '1';
            group.style.transform = 'translateY(0)';
        }, 100 * index);
    });
});