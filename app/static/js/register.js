document.addEventListener("DOMContentLoaded", () => {
    const signUpBtn = document.getElementById("SignUpBtn");

    signUpBtn.addEventListener("click", async (event) => {
        event.preventDefault(); // stop page reload

        const inputs = document.querySelectorAll(".input-field");
        const username = inputs[0].value.trim();
        const phone = inputs[1].value.trim();
        const email = inputs[2].value.trim();
        const password = inputs[3].value.trim();
        const confirmPassword = inputs[4].value.trim();

        // validation
        if (!username || !phone || !email || !password || !confirmPassword) {
            alert("Please fill in all fields.");
            return;
        }

        if (password !== confirmPassword) {
            alert("Passwords do not match!");
            return;
        }

        if (!document.getElementById("agree").checked) {
            alert("You must agree to the terms & conditions.");
            return;
        }

        try {
            const response = await fetch("/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, phone, email, password })
            });

            const result = await response.json();

            if (response.ok) {
                alert("Registration successful! Please log in.");
                window.location.href = "index.html"; // ✅ redirect to login page
            } else {
                alert(result.error || "Registration failed.");
            }

        } catch (err) {
            console.error("Error:", err);
            alert("Something went wrong. Please try again later.");
        }
    });
});
