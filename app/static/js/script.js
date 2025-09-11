document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.querySelector(".submit-btn");

    submitBtn.addEventListener("click", async (event) => {
        event.preventDefault(); // stop form reload

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!email || !password) {
            alert("Please enter both email and password.");
            return;
        }

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (response.ok) {
                // login successful → redirect to home
                window.location.href = "/";
            } else {
                // login failed → show error
                alert(result.error || "Login failed. Please try again.");
            }

        } catch (err) {
            console.error("Error:", err);
            alert("Something went wrong. Please try again later.");
        }
    });
});
