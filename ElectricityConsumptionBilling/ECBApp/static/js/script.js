document.addEventListener("DOMContentLoaded", () => {
    const themeToggleButton = document.getElementById("theme-toggle");
    const sunIcon = themeToggleButton.querySelector(".fa-sun");
    const moonIcon = themeToggleButton.querySelector(".fa-moon");

    // Load the saved theme from localStorage (default is light)
    const currentTheme = localStorage.getItem("theme") || "light";
    document.body.setAttribute("data-theme", currentTheme);

    // Update icon visibility based on the current theme
    updateIcons(currentTheme);

    // Toggle theme on button click
    themeToggleButton.addEventListener("click", () => {
        const currentTheme = document.body.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";

        document.body.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);

        updateIcons(newTheme); // Update icons when theme changes
    });

    // Function to update sun and moon icons based on the current theme
    function updateIcons(theme) {
        if (theme === "dark") {
            sunIcon.classList.remove("hidden");
            moonIcon.classList.add("hidden");
        } else {
            sunIcon.classList.add("hidden");
            moonIcon.classList.remove("hidden");
        }
    }
});
