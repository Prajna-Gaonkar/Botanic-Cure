document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.querySelector("form");
    const signUpBtn = document.getElementById("SignUpBtn");

    registerForm.addEventListener("submit", (event) => {
        // Client-side validation
        const password = document.querySelector('input[name="password"]').value;
        const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
        
        if (password !== confirmPassword) {
            event.preventDefault();
            alert("Passwords do not match!");
            return;
        }

        if (!document.getElementById("agree").checked) {
            event.preventDefault();
            alert("You must agree to the terms & conditions.");
            return;
        }

        // Disable button to prevent double submission
        signUpBtn.disabled = true;
        signUpBtn.textContent = "Creating Account...";

        // Re-enable after 2 seconds in case of error
        setTimeout(() => {
            signUpBtn.disabled = false;
            signUpBtn.textContent = "Sign Up";
        }, 2000);
    });
});
