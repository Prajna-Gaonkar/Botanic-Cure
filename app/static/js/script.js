document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.querySelector("form");
    const submitBtn = loginForm.querySelector(".submit-btn");
    
    loginForm.addEventListener("submit", async (event) => {
        // Don't prevent default form submission - let the form submit normally
        // This allows the server to handle the response and flash messages
        
        // Disable the submit button to prevent double submission
        submitBtn.disabled = true;
        submitBtn.textContent = "Signing in...";

        // Re-enable the button after 2 seconds (in case of error)
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = "Sign In";
        }, 2000);
    });
});
